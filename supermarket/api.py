import re
import operator

from flask import Blueprint, request
from flask_restful import Api, Resource as BaseResource
from werkzeug.exceptions import HTTPException

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
        field = field.strip()
        model = self.model
        relation = None
        keys = []
        if '.' in field:
            keys = field.split('.')
            field = keys.pop(0)
        elif field in self.schema().related_fields:
            field = '{}_id'.format(field)

        if (field in self.schema().nested_fields +
                self.schema().related_fields + self.schema().related_lists):
            relation = getattr(model, field)
            field = keys.pop(0) if keys else 'id'
            model = relation.property.mapper.class_

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
        return self._default_filter

    def _default_filter(self, query, field, op, value):
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
        if not only_fields:
            return only_fields
        sanitized = []
        for field in only_fields.split(','):
            field = field.strip()
            if field in self.schema().fields:
                sanitized.append(field)
        return sanitized

    def _pagination_info(self, page):
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

    def get_item(self, id):
        """Get an item of ‘type’ by ‘ID’."""
        r = self.model.query.get_or_404(id)
        return self.schema().dump(r).data, 200

    def patch_item(self, id):
        """Update an existing item with new data."""
        r = self.model.query.get_or_404(id)
        data = self.schema().load(request.get_json(),
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
        r.id = id
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
        - <fieldname>: filter by the given value (using equal),
        - <fieldname>:<operator>: filter using the given operator,
                                  accepts 'lt', 'le', 'eq', 'ne', 'ge', 'gt', 'in' and 'like'
        """
        # get arguments from query parameters
        args = request.args.copy()
        page = int(args.pop('page', 1))
        limit = int(args.pop('limit', 20))
        sort = args.pop('sort', 'name')
        only = self._sanitize_only(args.pop('only', None))
        errors = []

        # get data from model
        query = self.model.query
        query = self._sort(query, sort, errors)
        query = self._filter(query, args, errors)
        page = query.paginate(page=page, per_page=limit)

        return {
            'items': self.schema(many=True, only=only).dump(page.items).data,
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

    """Has additional label specifc filters."""

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
