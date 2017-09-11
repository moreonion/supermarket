import re
import operator

from flask import Blueprint, request
from flask_restful import Api, Resource as BaseResource
from werkzeug.exceptions import HTTPException
from werkzeug.datastructures import MultiDict
from sqlalchemy.inspection import inspect

import supermarket.model as m
import supermarket.schema as s

app = Blueprint('api', __name__)
api = Api(app)


# Custom errors

class ValidationFailed(HTTPException):

    """Raised when schema validation fails.

    All ValidationErrors are put in a consistent error message format
    for a ‘400 Bad request’ response.

    :param dict errors       Errors dict as returned by Marshmellow schema_load().
    :param str description   Error message, defaults to "Validation Error".

    """

    code = 400
    data = {}

    def __init__(self, errors, description='Validation error.'):
        super().__init__()
        self.data['message'] = description
        self.data['errors'] = []
        for f, msg in errors.items():
            self.data['errors'].append({'field': f, 'messages': msg})


class ParamException(Exception):

    """Raised when an URL parameter cannot be applied.

    :param str message      Error message to display.

    """

    def __init__(self, message, *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)


class FilterOperatorException(ParamException):

    """Raised when a field cannot be filtered because the operator doesn't make sense.

    :param str op           Name of the operator that triggered the exception.
    :param list accepted    List of accepted operators.

    """

    def __init__(self, op, accepted, *args, **kwargs):
        self.message = 'Unknown operator `{}`, try one of `{}`.'.format(op, ', '.join(accepted))
        super(ParamException).__init__(*args, **kwargs)


# Resources

class GenericResource:

    """Bundles generic behaviour for all resources.

    Attributes:
        model       The :class:`~flask_sqlalchemy.Model` to query and save to.
        schema      The :class:`~supermarket.schema.CustomSchema` associated with the model.

    """

    def __init__(self, model, schema):
        self.model = model
        self.schema = schema

    def _field_to_attr(self, field, query):
        # Get the attribute of a model class by field name and update the query if necessary.
        #
        # Returns a :class:`~sqlalchemy.orm.attributes.InstrumentedAttribute` matching
        # the field name and the query joined with the table that contains the attribute.
        # Raises a :class:`~supermarket.api.ParamException` if the field can’t be matched.
        #
        # :param str field  Field name, may include subfield names joined with ‘.’ for
        #                   JSON fields or one level of nested and related fields.
        # :param obj query  Query of type :class:`~flask_sqlalchemy.BaseQuery` to update.
        #
        field = field.strip()
        model = self.model
        schema = self.schema
        relation = None
        keys = []
        if '.' in field:
            keys = field.split('.')
            field = keys.pop(0)
        elif field in schema().related_fields:
            field = '{}_id'.format(field)

        if field in schema().nested_fields:
            schema = schema().fields[field].nested
            if isinstance(schema, str):
                schema = s.class_registry.get_class(schema)
            model = getattr(model, field).property.mapper.class_
            field = keys.pop(0) if keys else inspect(model).primary_key[0].name

        if field in schema().related_fields + schema().related_lists:
            relation = getattr(model, field)
            model = relation.property.mapper.class_
            field = keys.pop(0) if keys else inspect(model).primary_key[0].name

        attr = getattr(model, field, None)
        if not hasattr(attr, 'type'):  # not a proper column
            attr = None
        elif isinstance(attr.type, m.JSONB) and keys:
            attr = attr[[k for k in keys]].astext
        elif keys:  # not a perfect match after all
            attr = None

        if attr is None:
            raise ParamException(
                'Unknown field `{}` for `{}`.'.format(field, model.__tablename__))
        if relation:
            query = query.outerjoin(relation)

        return (attr, query)

    def _find_filter(self, field):
        # Defines which filter method should be used for `field`.
        #
        # Allows child classes to add their own filters.
        #
        # :param str field      Name of the field to filter.
        #
        return self._default_filter

    def _default_filter(self, query, field, op, value):
        # Default filter method, filters `field` by `value` using `op`.
        #
        # Returns the filtered query.
        # Raises a :class:`~supermarket.api.ParamException` if the filter can’t be applied.
        #
        # :param obj query      Query of type :class:`~flask_sqlalchemy.BaseQuery` to filter.
        # :param str field      Name of the field to filter, may be formated as ‘field.subfield’.
        # :param str op         Operator to use for filtering,
        #                       accepts ‘lt’, ‘le’, ‘eq’, ‘ne’, ‘ge’, ‘gt’, ‘in’, ‘like’.
        # :param str value      Value to filter by.
        #
        accepted_operators = ['lt', 'le', 'eq', 'ne', 'ge', 'gt', 'in', 'like']
        (attr, query) = self._field_to_attr(field, query)
        if op not in accepted_operators:
            raise FilterOperatorException(op, accepted_operators)
        if op == 'like':
            if not (isinstance(attr.type, m.db.String) or isinstance(attr.type, m.db.Text)):
                raise ParamException('Can’t compare {type} to string.'.format(
                    type=attr.type.__class__.__name__.lower()))
            value = '%{}%'.format(value)
            query = query.filter(attr.ilike(value))
        elif op == 'in':
            values = [v.strip() for v in value.split(',')] if ',' in value else [value]
            query = query.filter(attr.in_(values))
        else:
            op = getattr(operator, op)
            query = query.filter(op(attr, value))
        return query

    def _filter(self, query, filter_fields, errors):
        # Go through `filter_fields` and apply a matching filter to the `query`.
        #
        # Adds any errors to `errors` and returns the filtered query.
        #
        # :param obj query            Query of type :class:`~flask_sqlalchemy.BaseQuery` to filter.
        # :param dict filter_fields   A :class:`~werkzeug.datastructures.MultiDict` containing
        #                             request parameters to be regarded as filters.
        # :param dict errors          Collection where caught errors should be added.
        #
        not_filtered = []
        for key, value in filter_fields.items(multi=True):
            (field, op) = key.split(':') if ':' in key else (key, 'eq')
            filter = self._find_filter(field)
            try:
                query = filter(query, field, op, value)
            except ParamException as pe:
                not_filtered.append({
                    'param': key,
                    'message': str(pe.message)
                })
        if not_filtered:
            errors.append({
                'errors': not_filtered,
                'message': 'Some parameters have been ignored.'
            })
        return query

    def _sort(self, query, sort_fields, errors):
        # Go through `sort_fields` and sort the `query` accordingly.
        #
        # Adds any errors to `errors` and returns the sorted query.
        #
        # :param obj query           Query of type :class:`~flask_sqlalchemy.BaseQuery` to filter.
        # :param str sort_fields     The field name, or multiple field names seperated by ‘,’,
        #                            to sort by, may be preceeded by ‘-’ to sort decending.
        # :param dict errors         Collection where caught errors should be added.
        #
        if not sort_fields:
            return query
        fields = []
        not_sorted = []
        for value in sort_fields.split(','):
            field = value.split('-')[-1]
            order = 'desc' if value[0] == '-' else 'asc'
            try:
                (attr, query) = self._field_to_attr(field, query)
                if order == 'desc':
                    attr = attr.desc()
                fields.append(attr)
            except ParamException as pe:
                not_sorted.append({
                    'value': value,
                    'message': pe.message
                })
        if not_sorted:
            errors.append({
                'errors': not_sorted,
                'message': 'Some values have been ignored for sorting.'
            })
        return query.order_by(*fields)

    def _sanitize_only(self, only_fields):
        # Converts a string of field names to a list of valid existing field names.
        if not only_fields:
            return only_fields
        sanitized = []
        for field in only_fields.split(','):
            field = field.strip()
            if field in self.schema().fields:
                sanitized.append(field)
        return sanitized

    def _pagination_info(self, page):
        # Get information from a :class:`~flask_sqlalchemy.Pagination` for later use as JSON.
        prev_url = re.sub(
            'page=\d+', 'page={}'.format(page.prev_num), request.url) if page.has_prev else False
        next_url = False
        if page.has_next:
            if 'page=' in request.url:
                next_url = re.sub('page=\d+', 'page={}'.format(page.next_num), request.url)
            elif request.args:
                next_url = '{}&page={}'.format(request.url, page.next_num)
            else:
                next_url = '{}?page={}'.format(request.url, page.next_num)
        pages = {
            'total': page.pages,
            'current': page.page,
            'next': page.next_num or False,
            'prev': page.prev_num or False,
            'next_url': next_url,
            'prev_url': prev_url
        }
        return pages

    def _parse_include_params(self, query, include_fields, errors):
        # Go through `include_fields` (fields that should be nested) and retrieve their schema.
        #
        # :params str include_fields   The raw parameter value: a comma seperated list of fields
        #                              to nest, in the form <field>.<attr> or <field>.all
        # :returns   A dictionary containing the schema and fields.
        #
        include_raw = include_fields.split(',')
        include = MultiDict()
        included = {}
        not_included = []

        # check valid format and collect fields in MultiDict
        for i in [i.strip().rsplit('.', maxsplit=1) for i in include_raw]:
            if len(i) == 2:
                include.add(*i)
            else:
                not_included.append({
                    'value': '.'.join(i),
                    'message': 'Invalid format.'
                })

        # loop through fields
        for relation, fields in include.lists():
            # check for superfluous fields
            if 'all' in fields:
                fields.remove('all')
                for f in fields:
                    not_included.append({
                        'value': '.'.join([relation, f]),
                        'message': 'Ignored because `{}.all` makes it obsolete.'.format(relation)
                    })
                fields = ['all']
            # get attr of related field
            related_field = relation
            if relation in self.schema().related_fields:
                related_field = relation + inspect(self.model).primary_key[0].name
            try:
                attr = self._field_to_attr(related_field, query)[0]  # no need to update the query
            except ParamException as e:
                for f in fields:
                    not_included.append({
                        'value': '.'.join([relation, f]),
                        'message': e.message
                    })
                continue
            # find the matching resource
            resource = next(filter(lambda v: v.model.__table__ == attr.table, resources.values()))
            # make sure all fields in `only` are valid and only ‘all’ becomes an empty list.
            only = []
            if fields != ['all']:
                for f in fields:
                    if f in resource.schema().fields:
                        only.append(f)
                    else:
                        not_included.append({
                            'value': '.'.join([relation, f]),
                            'message': 'Unknown field `{}` for `{}`.'.format(
                                f, resource.model.__tablename__)
                        })
                if not only:
                    continue
            # everything seems fine, add field to `ìncluded`
            included[relation.rpartition('.')[2]] = {'resource': resource, 'only': only}

        if not_included:
            errors.append({
                'errors': not_included,
                'message': 'Some values have been not been included.'
            })
        return included

    def get_item(self, id):
        """Get an item of ‘type’ by ‘ID’."""
        r = self.model.query.get_or_404(id)
        errors = []
        query = self.model.query
        args = request.args.copy()
        only = self._sanitize_only(args.pop('only', None))
        include = args.pop('include', '')
        schema = self.schema(only=only)
        if include:
            schema.context['include'] = self._parse_include_params(query, include, errors)

        return {
            'item': schema.dump(r).data,
            'errors': errors
        }, 200

    def patch_item(self, id):
        """Update an existing item with new data."""
        r = self.model.query.get_or_404(id)
        data = self.schema().load(request.get_json(), partial=True,
                                  session=m.db.session, instance=r)
        if data.errors:
            raise ValidationFailed(data.errors)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    def put_item(self, id):
        """Add a new item if the ID doesn’t exist, or replace the existing one."""
        data = self.schema().load(request.get_json(), session=m.db.session)
        if data.errors:
            raise ValidationFailed(data.errors)
        r = data.data
        setattr(r, inspect(self.model).primary_key[0].name, id)
        m.db.session.merge(r)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    def delete_item(self, id):
        """Delete an item of ‘type’ by its ID."""
        r = self.model.query.get_or_404(id)
        m.db.session.delete(r)
        m.db.session.commit()
        return '', 204

    def get_list(self):
        """Get a paged list containing all items of type ‘type’.

        It's possible to amend the list with query parameters:
        - limit: maximum number of items per page (default 20)
        - page: which page to display (default 1)
        - only: comma seperated field names to return in the result (includes all fields if empty).
        - sort: comma seperated field names to sort by, preceed by '-' to sort descending.
        - include: comma seperated nested field names prepended by field name that includes IDs.
        - <fieldname>: filter by the given value (using equal),
        - <fieldname>:<operator>: filter using the given operator,
                                  accepts 'lt', 'le', 'eq', 'ne', 'ge', 'gt', 'in' and 'like'

        """
        # get arguments from query parameters
        args = request.args.copy()
        page = int(args.pop('page', 1))
        limit = int(args.pop('limit', 20))
        sort = args.pop('sort', None)
        include = args.pop('include', '')
        only = self._sanitize_only(args.pop('only', None))
        errors = []

        # get data from model
        query = self.model.query
        query = self._sort(query, sort, errors)
        query = self._filter(query, args, errors)
        page = query.paginate(page=page, per_page=limit)
        schema = self.schema(many=True, only=only)
        if include:
            schema.context['include'] = self._parse_include_params(query, include, errors)

        return {
            'items': schema.dump(page.items).data,
            'pages': self._pagination_info(page),
            'errors': errors
        }, 200

    def post_to_list(self):
        """Add a new item of type ‘type’."""
        data = self.schema().load(request.get_json(), session=m.db.session)
        if data.errors:
            raise ValidationFailed(data.errors)
        r = data.data
        m.db.session.add(r)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    def get_doc(self):
        """Get documentation for type ‘type’."""
        return self.schema().schema_description, 200


class LabelResource(GenericResource):

    """Has additional label specifc filters and include options."""

    def _find_filter(self, field):
        if field == 'hotspots':
            filter = self._hotspot_filter
        elif field == 'countries':
            filter = self._country_filter
        else:
            filter = super()._find_filter(field)
        return filter

    def _hotspot_filter(self, query, field, op, value):
        accepted_operators = ['eq', 'in']
        if op not in accepted_operators:
            raise FilterOperatorException(op, accepted_operators)
        hotspots = [v.strip() for v in value.split(',')] if ',' in value else [value]
        query = query.filter(self.model.id.in_(
            m.db.session.query(m.LabelMeetsCriterion.label_id)
            .join(m.LabelMeetsCriterion.criterion)
            .join(m.Criterion.improves_hotspots)
            .filter(m.CriterionImprovesHotspot.hotspot_id.in_(hotspots))
        ))
        return query

    def _country_filter(self, query, field, op, value):
        accepted_operators = ['eq', 'in']
        if op not in accepted_operators:
            raise FilterOperatorException(op, accepted_operators)
        countries = [v.strip() for v in value.split(',')] if ',' in value else [value]
        countries.append('*')  # include international labels
        query = query.join(self.model.countries).filter(m.LabelCountry.code.in_(countries))
        return query

    def _parse_include_params(self, query, include_fields, errors):
        # include hotspots, too
        include_raw = include_fields.split(',')
        hotspot_fields = []
        super_fields = []
        not_included = []
        for raw in include_raw:
            if raw.startswith('hotspots.') and len(raw.split('.')) == 2:
                hotspot_fields.append(raw.rpartition('.')[2])
            else:
                super_fields.append(raw)

        resource = resources['hotspots']
        only = []
        if 'all' in hotspot_fields:
            hotspot_fields.remove('all')
            for f in hotspot_fields:
                not_included.append({
                    'value': '.'.join(['hotspots', f]),
                    'message': 'Ignored because `hotspots.all` makes it obsolete.'
                })
        else:
            for f in hotspot_fields:
                if f in resource.schema().fields:
                    only.append(f)
                else:
                    not_included.append({
                        'value': '.'.join(['hotspots', f]),
                        'message': 'Unknown field `{}` for `hotspots`.'.format(f)
                    })
            if not only:
                only = None

        included = super()._parse_include_params(query, ','.join(super_fields), errors)
        if only is not None:
            included['hotspots'] = {'resource': resource, 'only': only}

        if not_included:
            include_error = next((e for e in errors if e.message ==
                                  'Some values have been not been included.'), None)
            if include_error:
                include_error.errors.update(not_included)
            else:
                errors.append({
                    'errors': not_included,
                    'message': 'Some values have been not been included.'
                })
        return included


resources = {
    'brands': GenericResource(m.Brand, s.Brand),
    'categories': GenericResource(m.Category, s.Category),
    'criteria': GenericResource(m.Criterion, s.Criterion),
    'hotspots': GenericResource(m.Hotspot, s.Hotspot),
    'labels': LabelResource(m.Label, s.Label),
    'origins': GenericResource(m.Origin, s.Origin),
    'producers': GenericResource(m.Producer, s.Producer),
    'products': GenericResource(m.Product, s.Product),
    'resources': GenericResource(m.Resource, s.Resource),
    'retailers': GenericResource(m.Retailer, s.Retailer),
    'stores': GenericResource(m.Store, s.Store),
    'suppliers': GenericResource(m.Supplier, s.Supplier),
    'supplies': GenericResource(m.Supply, s.Supply)
}


@api.resource('/<any({}):type>/<int:id>'.format(', '.join(resources)))
class ResourceItem(BaseResource):

    """A resource item of type ‘type’, identified by its ID."""

    def get(self, type, id):
        return resources[type].get_item(id)

    def patch(self, type, id):
        return resources[type].patch_item(id)

    def put(self, type, id):
        return resources[type].put_item(id)

    def delete(self, type, id):
        return resources[type].delete_item(id)


@api.resource('/<any({}):type>'.format(', '.join(resources)))
class ResourceList(BaseResource):

    """A list of resources of type ‘type’."""

    def get(self, type):
        return resources[type].get_list()

    def post(self, type):
        return resources[type].post_to_list()


@api.resource('/doc/<any({}):type>'.format(', '.join(resources)))
class ResourceDoc(BaseResource):

    """API documentation for resources of type ‘type’."""

    def get(self, type):
        return resources[type].get_doc()
