from flask import Blueprint, request
from flask_restful import Api, Resource as BaseResource

import supermarket.model as m
import supermarket.schema as s

app = Blueprint('api', __name__)
api = Api(app)


# Custom errors and responses

class ValidationFailed(Exception):

    """Raised when schema validation fails.

    All ValidationErrors are put in a consistent error message format
    for a ‘400 Bad request’ response.

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


# Resources

resources = {
    'products': {'model': m.Product, 'schema': s.Product}
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
        data = self.schema().load(request.get_json(), instance=r)
        if data.errors:
            raise ValidationFailed(data.errors)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    def put(self, type, id):
        """Add a new item if the ID doesn’t exist, or replace the existing one."""
        self._set_resource(type)
        data = self.schema().load(request.get_json())
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

    def get(self, type):
        """Get a list containing all items of type ‘type’."""
        self._set_resource(type)
        list = self.model.query.all()
        return self.schema(many=True).dump(list).data, 200

    def post(self, type):
        """Add a new item of type ‘type’."""
        self._set_resource(type)
        data = self.schema().load(request.get_json())
        if data.errors:
            raise ValidationFailed(data.errors)
        r = data.data
        m.db.session.add(r)
        m.db.session.commit()
        return self.schema().dump(r).data, 201
