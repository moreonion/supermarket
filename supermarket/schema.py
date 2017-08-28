from flask import url_for
from flask_marshmallow import Marshmallow
from flask_marshmallow.fields import _rapply as ma_rapply
from marshmallow import post_load, validates_schema, ValidationError
from marshmallow_sqlalchemy import fields as masqla_fields

import supermarket.model as m

ma = Marshmallow()


# Custom (overridden) fields

class HyperlinkRelated(ma.HyperlinkRelated):

    """Field that generates hyperlinks to indicate references between models.

    Like :class:`~flask_marshmallow.sqla.HyperlinkRelated`, but takes additional
    resource parameters for `flask.url_for` and returns `None` if there is no URL.

    :param str endpoint    Flask endpoint name for generated hyperlink.
    :param dict params     Parameters for the api resource
    :param str url_key     The attribute containing the reference's primary key. Defaults to "id".
    :param bool external   Set to `True` if absolute URLs should be used, instead of relative URLs.

    """

    def __init__(self, endpoint, params=None, url_key='id', external=False, **kwargs):
        super().__init__(endpoint, url_key, external, **kwargs)
        self.params = params

    def _serialize(self, value, attr, obj):
        if not value:
            return None  # There’s nothing there to get a URL for

        key = super(ma.HyperlinkRelated, self)._serialize(value, attr, obj)
        if key is None:
            return None  # Can’t build URL without key

        kwargs = {self.url_key: key}
        kwargs.update(self.params)
        return url_for(self.endpoint, _external=self.external, **kwargs)


class HyperlinkRelatedList(HyperlinkRelated):

    """Field that generates hyperlinks to indicate references between models.

    Like :class:¸~supermarket.schema.HyperlinkRelated`, but used for "many" relationships.
    Instead of returning a link to a single related item, it returns a link to a filtered list.

    :param str endpoint    Flask endpoint name for generated hyperlink.
    :param dict params     Parameters for the api resource
    :param str url_key     The attribute containing the reference's filter key. Defaults to "id".
    :param bool external   Set to `True` if absolute URLs should be used, instead of relative URLs.

    """

    def __init__(self, endpoint, params=None, url_key='id', external=False, **kwargs):
        if url_key != 'id':
            kwargs.update({'column': url_key})
        super().__init__(endpoint, params, url_key, external, **kwargs)

    def _serialize(self, value, attr, obj):
        keys = set(super(ma.HyperlinkRelated, self)._serialize(val, attr, obj) for val in value)
        if not keys:
            return None  # Can’t build URL without keys

        kwargs = {self.url_key: ','.join(map(str, keys))}
        kwargs.update(self.params)
        return url_for(self.endpoint, _external=self.external, **kwargs)


class Hyperlinks(ma.Hyperlinks):

    """Field that outputs a dictionary of hyperlinks.

    Like :class:`~flask_marshmallow.fields.Hyperlinks,`
    but also excepts :class:¸~supermarket.schema.HyperlinkRelated` objects as values.

    :param dict schema    A dict that maps names to
                          :class:`~flask_marshmallow.fields.URLFor` or
                          :class:¸~supermarket.schema.HyperlinkRelated` fields.
    """

    def _serialize(self, value, attr, obj):

        def _url_val(val, key, obj, **kwargs):
            val.parent = self.parent
            if isinstance(val, ma.URLFor) or isinstance(val, HyperlinkRelated):
                return val.serialize(key, obj, **kwargs)
            else:
                return val

        return ma_rapply(self.schema, _url_val, key=attr, obj=obj)


# Custom (overriden) base schema

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

    @property
    def schema_description(self):
        """Document the schema."""
        # TODO: better description for NestedFields, MethodFields
        fields = {}
        links = self.fields['links'].schema if 'links' in self.fields else None
        for k, v in self.fields.items():
            type = v.container if isinstance(v, ma.List) else v
            d = {
                'type': type.__class__.__name__.lower(),
                'required': v.required,
                'read-only': v.dump_only,
                'list': isinstance(v, ma.List)
            }
            if k in self.related_fields + self.related_lists:
                if links and 'related' in links and k in links['related']:
                    link = self.fields['links'].schema['related'][k]
                    d['doc'] = url_for('api.resourcedoc', _external=True, **link.params)
                else:
                    d['doc'] = False
            fields[k] = d
        list = self.fields['links'].schema['list']
        list_url = url_for(list.endpoint, **list.params)
        return {'fields': fields, 'link': list_url}

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
        dump_only = ['id', 'links']  # read-only properties, will be ignored when loading


# Supermarket schemas

class Brand(CustomSchema):
    # id, name
    # refs: retailer, products, stores
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='brands', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='brands', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='brands', _external=True),
        'related': {
            'retailer': HyperlinkRelated(
                'api.resource', {'type': 'retailers'}, external=True, attribute='retailer'),
            'stores': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'stores'}, external=True, attribute='stores',
                url_key='brand_id'),
            'products': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'products'}, external=True, attribute='products',
                url_key='brand_id')
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Brand


class Category(CustomSchema):
    # id, name
    # refs: products
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='categories', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='categories', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='categories', _external=True),
        'related': {
            'products': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'products'}, external=True, attribute='products',
                url_key='category_id')
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Category


class Criterion(CustomSchema):
    # id, name, type (label, retailer), code, details (JSONB)
    # refs: improves_hotspots
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='criteria', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='criteria', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='criteria', _external=True),
        'related': {
            # TODO: improves_hotspots
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Criterion


class Hotspot(CustomSchema):
    # id, name, description
    # refs: scores
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='hotspots', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='hotspots', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='hotspots', _external=True),
        'related': {
            # TODO: scores
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Hotspot


class LabelMeetsCriterion(CustomSchema):
    # primary key: label_id + criterion_id
    # score, explanation
    # refs: criterion, label
    criterion = ma.Nested(Criterion, only=('id', 'links', 'code', 'name', 'details'))

    class Meta(CustomSchema.Meta):
        model = m.LabelMeetsCriterion


class Label(CustomSchema):
    # id, name, type (product, retailer), description, details (JSONB), logo
    # refs: meets_criteria, resources, products, retailers
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='labels', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='labels', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='lables', _external=True),
        'related': {
            # TODO: meets_criteria
            'products': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'products'}, external=True, attribute='products'),
            'resources': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'resources'}, external=True, attribute='resources'),
            'retailers': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'retailers'}, external=True, attribute='retailers')
        }
    })
    meets_criteria = ma.Nested(LabelMeetsCriterion, many=True)
    hotspots = ma.Method('get_hotspots', dump_only=True)

    def get_hotspots(self, m):
        hs = Hotspot(only=('id', 'name', 'links'))
        hotspots = set()
        for mc in m.meets_criteria:
            for ih in mc.criterion.improves_hotspots:
                hotspots.add(ih.hotspot)
        return [hs.dump(h).data for h in hotspots]

    class Meta(CustomSchema.Meta):
        model = m.Label


class Origin(CustomSchema):
    # id, name, code
    # refs: ingredients, supplies
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='origins', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='origins', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='origins', _external=True),
        'related': {
            # TODO: ingredients
            'supplies': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'supplies'}, external=True, attribute='supplies')
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Origin


class Producer(CustomSchema):
    # id, name
    # refs: products
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='producers', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='producers', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='producers', _external=True),
        'related': {
            'products': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'products'}, external=True, attribute='products',
                url_key='producer_id')
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Producer


class Product(CustomSchema):
    # id, name, details (JSONB), gtin
    # refs: brand, category, prodcuer, ingredients, labels, stores
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='products', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='products', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='products', _external=True),
        'related': {
            'brand': HyperlinkRelated(
                'api.resource', {'type': 'brands'}, external=True, attribute='brand'),
            'category': HyperlinkRelated(
                'api.resource', {'type': 'categories'}, external=True, attribute='category'),
            'producer': HyperlinkRelated(
                'api.resource', {'type': 'producers'}, external=True, attribute='producer'),
            'labels': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'labels'}, external=True, attribute='labels'),
            'stores': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'stores'}, external=True, attribute='stores')
            # TODO: ingredients
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Product


class Resource(CustomSchema):
    # id, name
    # refs: ingredients, labels, supplies
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='resources', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='resources', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='resources', _external=True),
        'related': {
            # TODO: ingredients
            'labels': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'labels'}, external=True, attribute='labels'),
            'supplies': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'supplies'}, external=True, attribute='supplies',
                url_key='resource_id')
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Resource


class Retailer(CustomSchema):
    # id, name
    # refs: meets_criteria, brands, stores, labels
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='retailers', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='retailers', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='retailers', _external=True),
        'related': {
            # TODO: meets_criteria
            'brands': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'brands'}, external=True, attribute='brands',
                url_key='retailer_id'),
            'stores': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'stores'}, external=True, attribute='stores',
                url_key='retailer_id'),
            'labels': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'labels'}, external=True, attribute='labels')
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Retailer


class Store(CustomSchema):
    # id, name
    # refs: retailer, brands, products
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='stores', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='stores', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='stores', _external=True),
        'related': {
            'retailer': HyperlinkRelated(
                'api.resource', {'type': 'retailers'}, external=True, attribute='retailer'),
            'brands': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'brands'}, external=True, attribute='brands'),
            'products': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'products'}, external=True, attribute='products')
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Store


class Supplier(CustomSchema):
    # id, name
    # refs: ingredients, supplies
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='suppliers', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='suppliers', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='suppliers', _external=True),
        'related': {
            # TODO: ingredients
            'supplies': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'supplies'}, external=True, attribute='supplies',
                url_key='supplier_id')
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Supplier


class Supply(CustomSchema):
    # id
    # refs: resource, origin, supplier, scores
    links = Hyperlinks({
        'self': ma.URLFor('api.resource', type='supplies', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='supplies', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='supplies', _external=True),
        'related': {
            'resource': HyperlinkRelated(
                'api.resource', {'type': 'resources'}, external=True, attribute='resource'),
            'origin': HyperlinkRelated(
                'api.resource', {'type': 'origins'}, external=True, attribute='origin'),
            'supplier': HyperlinkRelated(
                'api.resource', {'type': 'suppliers'}, external=True, attribute='supplier')
            # TODO: scores
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Supply
