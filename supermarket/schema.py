from flask_marshmallow import Marshmallow
from marshmallow import validates_schema, ValidationError
import supermarket.model as m

ma = Marshmallow()


class ProductSchema(ma.ModelSchema):
    class Meta:
        model = m.Product

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        unknown = set(original_data) - set(self.fields)
        if unknown:
            raise ValidationError('Unknown field.', unknown)
