from flask import Blueprint, request
from flask_restful import Resource, Api

import supermarket.model as m
import supermarket.schema as s

app = Blueprint('api', __name__)
api = Api(app)

product_schema = s.ProductSchema()
product_list_schema = s.ProductSchema(many=True)


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

class Product(Resource):
    def get(self, product_id):
        p = m.Product.query.get_or_404(product_id)
        return product_schema.dump(p).data, 200

    def patch(self, product_id):
        p = m.Product.query.get_or_404(product_id)
        data = product_schema.load(request.get_json(), instance=p)
        if data.errors:
            raise ValidationFailed(data.errors)
        m.db.session.commit()
        return product_schema.dump(p).data, 201

    def put(self, product_id):
        data = product_schema.load(request.get_json())
        if data.errors:
            raise ValidationFailed(data.errors)
        p = data.data
        p.id = product_id
        m.db.session.merge(p)
        m.db.session.commit()
        return product_schema.dump(p).data, 201

    def delete(self, product_id):
        p = m.Product.query.get_or_404(product_id)
        m.db.session.delete(p)
        m.db.session.commit()
        return '', 204


class ProductList(Resource):
    def get(self):
        p_list = m.Product.query.all()
        return product_list_schema.dump(p_list).data, 200

    def post(self):
        data = product_schema.load(request.get_json())
        if data.errors:
            raise ValidationFailed(data.errors)
        p = data.data
        m.db.session.add(p)
        m.db.session.commit()
        return product_schema.dump(p).data, 201


api.add_resource(ProductList, '/products')
api.add_resource(Product, '/products/<int:product_id>')
