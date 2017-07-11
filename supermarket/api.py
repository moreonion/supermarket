from flask import Blueprint, request
from flask_restful import Resource, Api

import supermarket.model as m
import supermarket.schema as s

app = Blueprint('api', __name__)
api = Api(app)


# Custom errors and responses

class ValidationFailed(Exception):

    """Raise when schema validation fails.

    All ValidationErrors are put in a consistent error message format
    for a ‘Bad request’ response.

    :errors     Errors dict as returned by Marshmellow schema_load().

    """

    code = 400
    message = 'Validation failed.'

    def __init__(self, errors):
        super().__init__()
        self.errors = []
        for f, msg in errors.items():
            self.errors.append({'field': f, 'messages': msg})


@app.errorhandler(ValidationFailed)
def handle_validation_failed(e):
    return api.make_response(
        code=e.code,
        data={'messages': e.message, 'errors': e.errors}
    )


# Resource prototypes

class BaseResource(Resource):

    """Prototype for a resource item, identified by its ID.

    Attributes:
        model       The SQLAlchemy model to query and save to.
        schema      The Marshmallow schema associated with the model.
        path        The path suffix representing the resource.

    """

    model = None
    schema = None
    path = ''

    def get(self, id):
        """Get an item by ID."""
        r = self.model.query.get_or_404(id)
        return self.schema().dump(r).data, 200

    def patch(self, id):
        """Update an existing item with new data."""
        r = self.model.query.get_or_404(id)
        data = self.schema().load(request.get_json(), instance=r)
        if data.errors:
            raise ValidationFailed(data.errors)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    def put(self, id):
        """Add a new item if the ID doesn't exist, or replace the existing one."""
        data = self.schema().load(request.get_json())
        if data.errors:
            raise ValidationFailed(data.errors)
        r = data.data
        r.id = id
        m.db.session.merge(r)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    def delete(self, id):
        """Delete an item by its ID."""
        r = self.model.query.get_or_404(id)
        m.db.session.delete(r)
        m.db.session.commit()
        return '', 204

    @classmethod
    def add_resource(cls, api):
        """Add the path for the resource to an Api."""
        api.add_resource(cls, '{}/<int:id>'.format(cls.path))


class BaseResourceList(Resource):

    """Prototype for a resource list.

    Attributes:
        model       The SQLAlchemy model to query and save to.
        schema      The Marshmallow schema associated with the model.
        path        The path suffix representing the resource.

    """

    model = None
    schema = None
    path = ''

    def get(self):
        """Get a list containing all items."""
        list = self.model.query.all()
        return self.schema(many=True).dump(list).data, 200

    def post(self):
        """Add a new item."""
        data = self.schema().load(request.get_json())
        if data.errors:
            raise ValidationFailed(data.errors)
        r = data.data
        m.db.session.add(r)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    @classmethod
    def add_resource(cls, api):
        """Add the path for the resource to an Api."""
        api.add_resource(cls, cls.path)


# Actual resources

class Product(BaseResource):
    model = m.Product
    schema = s.Product
    path = '/products'


class ProductList(BaseResourceList):
    model = m.Product
    schema = s.Product
    path = '/products'


Product.add_resource(api)
ProductList.add_resource(api)
