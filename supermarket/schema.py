from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import fields as masqla_fields
from marshmallow import post_load, validates_schema, ValidationError
import supermarket.model as m

ma = Marshmallow()


class CustomSchema(ma.ModelSchema):

    """Config and validation that all our schemas share"""

    def _get_related_fields(self):
        fields = []
        for key, field in self.fields.items():
            if isinstance(field, masqla_fields.Related):
                fields.append(key)
        return fields

    def _get_related_lists(self):
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

        for field in self._get_related_fields():
            if field in data:
                item = data[field]
                if check(data[field]) is False:
                    errors[field] = ['There is no {} with id {}.'.format(field, data[field].id)]

        for list in self._get_related_lists():
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
    class Meta(CustomSchema.Meta):
        model = m.Brand


class Product(CustomSchema):
    class Meta(CustomSchema.Meta):
        model = m.Product
