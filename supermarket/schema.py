from flask_marshmallow import Marshmallow
import supermarket.model as m

ma = Marshmallow()

class ProductSchema(ma.ModelSchema):
    class Meta:
        model = m.Product
