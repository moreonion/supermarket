from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import fields as masqla_fields
from marshmallow import post_load, validates_schema, ValidationError
import supermarket.model as m

ma = Marshmallow()


class CustomSchema(ma.ModelSchema):

    """Config and validation that all our schemas share"""

    @property
    def related_fields(self):
        fields = []
        for key, field in self.fields.items():
            if isinstance(field, masqla_fields.Related):
                fields.append(key)
        return fields

    @property
    def related_lists(self):
        lists = []
        for key, field in self.fields.items():
            if (isinstance(field, ma.List) and
                    isinstance(field.container, masqla_fields.Related)):
                lists.append(key)
        return lists

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        """Do not accept (and silently ignore) fields that do not exist."""
        unknown = set(original_data) - set(self.fields)
        if unknown:
            raise ValidationError('Unknown field.', unknown)

    @post_load
    def check_related_fields(self, data):
        """Only except ids for related fields if an entry with this id exists in the database."""
        errors = {}

        def check(item):
            if hasattr(item, 'id'):
                return item.id is None or item.__class__.query.get(item.id) is not None
            return True

        for field in self.related_fields:
            if field in data:
                item = data[field]
                if check(data[field]) is False:
                    errors[field] = ['There is no {} with id {}.'.format(field, data[field].id)]

        for list in self.related_lists:
            if list in data:
                list_errors = []
                for item in data[list]:
                    if check(item) is False:
                        list_errors.append('There is no {} with id {}.'.format(list[:-1], item.id))
                if list_errors:
                    errors[list] = list_errors

        if errors:
            raise ValidationError(errors)

        return data

    class Meta:
        dump_only = ['id']  # read-only property, will be ignored when loading


class Brand(CustomSchema):
    # id, name
    # refs: retailer, products, stores

    class Meta(CustomSchema.Meta):
        model = m.Brand


class Category(CustomSchema):
    # id, name
    # refs: products

    class Meta(CustomSchema.Meta):
        model = m.Category


class Criterion(CustomSchema):
    # id, name, type (label, retailer), code, details (JSONB)
    # refs: improves_hotspots

    class Meta(CustomSchema.Meta):
        model = m.Criterion


class Hotspot(CustomSchema):
    # id, name, description
    # refs: scores

    class Meta(CustomSchema.Meta):
        model = m.Hotspot


class Label(CustomSchema):
    # id, name, type (product, retailer), description, details (JSONB), logo
    # meets_criteria, resources
    # refs: products, retailers

    class Meta(CustomSchema.Meta):
        model = m.Label


class Origin(CustomSchema):
    # id, name, code
    # refs: ingredients, supplies

    class Meta(CustomSchema.Meta):
        model = m.Origin


class Producer(CustomSchema):
    # id, name
    # refs: products

    class Meta(CustomSchema.Meta):
        model = m.Producer


class Product(CustomSchema):
    # id, name, details (JSONB), gtin
    # refs: brand, category, prodcuer, ingredients, labels, stores

    class Meta(CustomSchema.Meta):
        model = m.Product


class Resource(CustomSchema):
    # id, name
    # refs: ingredients, labels, supplies

    class Meta(CustomSchema.Meta):
        model = m.Resource


class Retailer(CustomSchema):
    # id, name
    # refs: meets_criteria, brands, stores, labels

    class Meta(CustomSchema.Meta):
        model = m.Retailer


class Store(CustomSchema):
    # id, name
    # refs: retailer, brands, products

    class Meta(CustomSchema.Meta):
        model = m.Store


class Supplier(CustomSchema):
    # id, name
    # refs: ingredients, supplies

    class Meta(CustomSchema.Meta):
        model = m.Supplier


class Supply(CustomSchema):
    # id
    # refs: resource, origin, supplier, scores
    # scores = Nested(Score, many=True)

    class Meta(CustomSchema.Meta):
        model = m.Supply
