from flask import Blueprint, request
from flask_restful import Resource, Api

import supermarket.model as m
import supermarket.schema as s

app = Blueprint('api', __name__)
api = Api(app)

product_schema = s.ProductSchema()
product_list_schema = s.ProductSchema(many=True)


class Product(Resource):
    def get(self, product_id):
        p = m.Product.query.get_or_404(product_id)
        return product_schema.dump(p).data, 200

    def put(self, product_id):
        p = m.Product.query.get_or_404(product_id)
        data = request.get_json()
        for k, v in data.items():
            setattr(p, k, v)
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
        data = request.get_json()
        p = m.Product(**data)
        m.db.session.add(p)
        m.db.session.commit()
        return product_schema.dump(p).data, 201


api.add_resource(ProductList, '/products')
api.add_resource(Product, '/products/<int:product_id>')
