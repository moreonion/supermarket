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


# Resources

resources = {
    'brands': {'model': m.Brand, 'schema': s.Brand},
    'categories': {'model': m.Category, 'schema': s.Category},
    'criteria': {'model': m.Criterion, 'schema': s.Criterion},
    'hotspots': {'model': m.Hotspot, 'schema': s.Hotspot},
    'labels': {'model': m.Label, 'schema': s.Label},
    'origins': {'model': m.Origin, 'schema': s.Origin},
    'producers': {'model': m.Producer, 'schema': s.Producer},
    'products': {'model': m.Product, 'schema': s.Product},
    'resources': {'model': m.Resource, 'schema': s.Resource},
    'retailers': {'model': m.Retailer, 'schema': s.Retailer},
    'stores': {'model': m.Store, 'schema': s.Store},
    'suppliers': {'model': m.Supplier, 'schema': s.Supplier},
    'supplies': {'model': m.Supply, 'schema': s.Supply}
}


@api.resource('/<any({}):type>/<int:id>'.format(', '.join(resources)))
class Resource(BaseResource):

    """A resource item of type ‘type’, identified by its ID.

    Attributes:
        model       The SQLAlchemy model to query and save to.
        schema      The Marshmallow schema associated with the model.

    """

    model = None
    schema = None

    def _set_resource(self, type):
        self.model = resources[type]['model']
        self.schema = resources[type]['schema']

    def get(self, type, id):
        """Get an item of ‘type’ by ‘ID’."""
        self._set_resource(type)
        r = self.model.query.get_or_404(id)
        return self.schema().dump(r).data, 200

    def patch(self, type, id):
        """Update an existing item with new data."""
        self._set_resource(type)
        r = self.model.query.get_or_404(id)
        data = self.schema().load(request.get_json(),
                                  session=m.db.session, instance=r)
        if data.errors:
            raise ValidationFailed(data.errors)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    def put(self, type, id):
        """Add a new item if the ID doesn’t exist, or replace the existing one."""
        self._set_resource(type)
        data = self.schema().load(request.get_json(), session=m.db.session)
        if data.errors:
            raise ValidationFailed(data.errors)
        r = data.data
        r.id = id
        m.db.session.merge(r)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    def delete(self, type, id):
        """Delete an item of ‘type’ by its ID."""
        self._set_resource(type)
        r = self.model.query.get_or_404(id)
        m.db.session.delete(r)
        m.db.session.commit()
        return '', 204


@api.resource('/<any({}):type>'.format(', '.join(resources)))
class ResourceList(BaseResource):

    """A list of resources of type ‘type’.

    Attributes:
        model       The SQLAlchemy model to query and save to.
        schema      The Marshmallow schema associated with the model.

    """

    model = None
    schema = None

    def _set_resource(self, type):
        self.model = resources[type]['model']
        self.schema = resources[type]['schema']

    def _sort(self, query, sort_fields, errors):
        if not sort_fields:
            return query
        fields = []
        not_sorted = []
        for field in sort_fields.split(','):
            if field[0] == '-':
                attr = self._field_to_attr(field[1:])
                if attr is not None:
                    fields.append(attr.desc())
                else:
                    not_sorted.append({
                        'value': field,
                        'message': 'Unknown field `{}`.'.format(field[1:])
                    })
            else:
                attr = self._field_to_attr(field)
                if attr is not None:
                    fields.append(attr)
                else:
                    not_sorted.append({
                        'value': field,
                        'message': 'Unknown field `{}`.'.format(field)
                    })
        if not_sorted:
            errors.append({
                'errors': not_sorted,
                'message': 'Some values have been ignored for sorting.'
            })
        return query.order_by(*fields)

    def _filter(self, query, filter_fields, errors):
        accepted_operators = ['lt', 'le', 'eq', 'ne', 'ge', 'gt', 'in', 'like']
        not_filtered = []

        for key, value in filter_fields.items(multi=True):
            (field, op) = key.split(':') if ':' in key else (key, 'eq')
            attr = self._field_to_attr(field)
            if attr is None:
                not_filtered.append({
                    'param': key,
                    'message': 'Unknown field `{}`.'.format(field)
                })
                continue
            elif op not in accepted_operators:
                not_filtered.append({
                    'param': key,
                    'message': 'Unknown operator `{op}`, try one of `{accepted}`.'.format(
                        op=op, accepted=', '.join(accepted_operators))
                })
                continue
            elif op == 'like':
                if not (isinstance(attr.type, m.db.String) or isinstance(attr.type, m.db.Text)):
                    not_filtered.append({
                        'param': key,
                        'message': 'Can’t compare {type} to string.'.format(
                            type=attr.type.__class__.__name__.lower())
                    })
                    continue
                value = '%{}%'.format(value)
                query = query.filter(attr.like(value))
            elif op == 'in':
                values = [v.strip() for v in value.split(',')] if ',' in value else [value]
                query = query.filter(attr.in_(values))
            else:
                op = getattr(operator, op)
                query = query.filter(op(attr, value))

        if not_filtered:
            errors.append({
                'errors': not_filtered,
                'message': 'Some parameters have been ignored.'
            })
        return query

    def _field_to_attr(self, field):
        field = field.strip()
        if field in self.schema().related_lists:
            return None  # can't sort or filter by lists
        if field in self.schema().related_fields:
            field = '{}_id'.format(field)
        if '.' in field:
            keys = field.split('.')
            a = getattr(self.model, keys.pop(0), None)
            if a and isinstance(a.type, m.JSONB):
                attr = a[[k for k in keys]].astext
        else:
            attr = getattr(self.model, field, None)
        return attr

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

    def get(self, type):
        """Get a paged list containing all items of type ‘type’.

        It's possible to amend the list with query parameters:
        - limit: maximum number of items per page (default 20)
        - page: which page to display (default 1)
        - only: comma seperated field names to return in the result (includes all fields if empty).
        - sort: comma seperated field names to sort by, preceed by '-' to sort descending.
        - <fieldname>: filter by the given value,
                       preceed by '<', '>', '<=', '=>' to use this operator instead of equals.
        """
        self._set_resource(type)

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

    def post(self, type):
        """Add a new item of type ‘type’."""
        self._set_resource(type)
        data = self.schema().load(request.get_json(), session=m.db.session)
        if data.errors:
            raise ValidationFailed(data.errors)
        r = data.data
        m.db.session.add(r)
        m.db.session.commit()
        return self.schema().dump(r).data, 201


@api.resource('/doc/<any({}):type>'.format(', '.join(resources)))
class ResourceDoc(BaseResource):

    """API documentation for resources of type ‘type’.

    Attributes:
        schema      The Marshmallow schema associated with the model.

    """

    def _set_resource(self, type):
        self.schema = resources[type]['schema']

    def get(self, type):
        """Get documentation for type ‘type’."""
        self._set_resource(type)
        return self.schema().schema_description, 200
