from flask import Blueprint, request
from flask_restful import Resource, Api

import supermarket.model as m
import supermarket.schema as s

app = Blueprint('api', __name__)
api = Api(app)


# Custom errors and responses

class ValidationFailed(Exception):
    code = 400
    message = 'Validation failed.'

    def __init__(self, fields):
        super().__init__()
        self.errors = []
        for f, msg in fields.items():
            self.errors.append({'field': f, 'messages': msg})


@app.errorhandler(ValidationFailed)
def handle_validation_failed(e):
    return api.make_response(
        code=e.code,
        data={'messages': e.message, 'errors': e.errors}
    )


# Resources

class BaseResource(Resource):
    model = None
    schema = None
    path = ''

    def get(self, id):
        r = self.model.query.get_or_404(id)
        return self.schema().dump(r).data, 200

    def patch(self, id):
        r = self.model.query.get_or_404(id)
        data = self.schema().load(request.get_json(), instance=r)
        if data.errors:
            raise ValidationFailed(data.errors)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    def put(self, id):
        data = self.schema().load(request.get_json())
        if data.errors:
            raise ValidationFailed(data.errors)
        r = data.data
        r.id = id
        m.db.session.merge(r)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    def delete(self, id):
        r = self.model.query.get_or_404(id)
        m.db.session.delete(r)
        m.db.session.commit()
        return '', 204

    @classmethod
    def add_resource(cls):
        api.add_resource(cls, '{}/<int:id>'.format(cls.path))


class BaseResourceList(Resource):
    model = None
    schema = None
    path = ''

    def get(self):
        list = self.model.query.all()
        return self.schema(many=True).dump(list).data, 200

    def post(self):
        data = self.schema().load(request.get_json())
        if data.errors:
            raise ValidationFailed(data.errors)
        r = data.data
        m.db.session.add(r)
        m.db.session.commit()
        return self.schema().dump(r).data, 201

    @classmethod
    def add_resource(cls):
        api.add_resource(cls, cls.path)


# make this part less redundant?

class Product(BaseResource):
    model = m.Product
    schema = s.Product
    path = '/products'


class ProductList(BaseResourceList):
    model = m.Product
    schema = s.Product
    path = '/products'


Product.add_resource()
ProductList.add_resource()
