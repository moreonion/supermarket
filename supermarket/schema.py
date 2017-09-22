from flask import url_for
from flask_marshmallow import Marshmallow
from flask_marshmallow.fields import _rapply as ma_rapply
from marshmallow_sqlalchemy import fields as masqla_fields
from marshmallow import (class_registry, pre_load, post_dump, post_load, utils,
                         validates_schema, ValidationError)
from sqlalchemy.inspection import inspect

import supermarket.model as m

ma = Marshmallow()


# Custom (overridden) fields

class Nested(ma.Nested):

    """Nested field that keeps the session when loading nested data.

    Fixes https://github.com/marshmallow-code/marshmallow-sqlalchemy/issues/67.

    """

    def _deserialize(self, value, attr, data):
        if self.many and not utils.is_collection(value):
            self.fail('type', input=value, type=value.__class__.__name__)
        session = self.parent.session
        data, errors = self.schema.load(value, session=session)
        if errors:
            raise ValidationError(errors, data=data)
        return data


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
    :param tuple url_key   The attribute name (see str) and another field name to use in the URL.
    :param bool external   Set to `True` if absolute URLs should be used, instead of relative URLs.

    """

    def __init__(self, endpoint, params=None, url_key='id', external=False, **kwargs):
        if utils.is_collection(url_key):
            kwargs.update({'column': url_key[0]})
            url_key = url_key[1]
        elif url_key != 'id':
            kwargs.update({'column': url_key})
        super().__init__(endpoint, params, url_key, external, **kwargs)

    def _serialize(self, value, attr, obj):
        keys = set(super(ma.HyperlinkRelated, self)._serialize(val, attr, obj) for val in value)
        if None in keys:
            keys.remove(None)
        if not keys:
            return None  # Can’t build URL without keys

        kwargs = {'{}:in'.format(self.url_key): ','.join(map(str, keys))}
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
            if isinstance(val, (ma.URLFor, HyperlinkRelated)):
                return val.serialize(key, obj, **kwargs)
            return val

        return ma_rapply(self.schema, _url_val, key=attr, obj=obj)


class Translated(masqla_fields.Related):

    """Multi language field."""

    def _serialize(self, value, attr, obj):
        lang = self.parent.language
        translation = list(filter(lambda t: t.language.value == lang, value))
        return None if len(translation) == 0 else translation[0].value

    def _deserialize(self, value, attr, data):
        lang = self.parent.language
        new_translation = self.related_model(language=lang, value=value, field=attr)
        parent_instance = self.parent.instance or self.parent.get_instance(data)

        if not parent_instance or not parent_instance.translation_id:
            return [new_translation]

        existing_strings = self.related_model.query.filter_by(
            translation_id=parent_instance.translation_id, field=attr).all()

        translation_index = next((i for i, t in enumerate(existing_strings)
                                 if t.language.value == lang), -1)
        if translation_index >= 0:
            existing_strings[translation_index].value = value
        else:
            new_translation.translation_id = parent_instance.translation_id
            existing_strings.append(new_translation)

        return existing_strings


# Custom (overriden) base schema

class CustomSchema(ma.ModelSchema):

    """Config and validation that all our schemas share."""

    language = 'en'  # default language

    def __init__(self, lang=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if lang:
            self.language = lang

    @property
    def nested_fields(self):
        """Get the keys of all fields of type `Nested`."""
        fields = []
        for key, field in self.fields.items():
            if isinstance(field, Nested):
                fields.append(key)
        return fields

    @property
    def translated_fields(self):
        """Get the keys of all fields that have a translation."""
        fields = []
        for key, field in self.fields.items():
            if isinstance(field, Translated):
                fields.append(key)
        return fields

    @property
    def related_fields(self):
        """Get the keys of all fields of type `Related`."""
        fields = []
        for key, field in self.fields.items():
            if isinstance(field, masqla_fields.Related) and key not in self.translated_fields:
                fields.append(key)
        return fields

    @property
    def related_lists(self):
        """Get the keys of all fields with a list of type `Related`."""
        lists = []
        for key, field in self.fields.items():
            if (isinstance(field, ma.List) and
                    isinstance(field.container, masqla_fields.Related)):
                lists.append(key)
        return lists

    @property
    def schema_description(self):
        """Document the schema."""
        fields = {}
        links = self.fields['links'].schema if 'links' in self.fields else None
        for k, v in self.fields.items():
            type = v.container if isinstance(v, ma.List) else v
            d = {
                'type': type.__class__.__name__.lower(),
                'required': v.required,
                'read-only': v.dump_only,
                'list': isinstance(v, ma.List) or (isinstance(v, Nested) and v.many)
            }
            if k in self.nested_fields:
                if isinstance(self.fields[k].nested, str):
                    nested_schema = class_registry.get_class(self.fields[k].nested)
                else:
                    nested_schema = self.fields[k].nested
                nested_schema = nested_schema(
                    only=self.fields[k].only,
                    exclude=self.fields[k].exclude
                )
                d.update(nested_schema.schema_description)
            if k in self.related_fields + self.related_lists:
                if links and 'related' in links and k in links['related']:
                    link = self.fields['links'].schema['related'][k]
                    d['doc'] = url_for('api.resourcedoc', _external=True, **link.params)
                else:
                    d['doc'] = False
            fields[k] = d
        list_url = False
        if links and 'list' in links:
            list_url = url_for(links['list'].endpoint, **links['list'].params)
        fields['language'] = {
            'type': 'string', 'required': False, 'read-only': True, 'list': False}
        return {'fields': fields, 'link': list_url}

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        """Do not accept (and silently ignore) fields that do not exist."""
        if self.many and utils.is_collection(original_data):
            for od in original_data:
                self.check_unknown_fields(data, od)
            return
        unknown = set(original_data) - set(self.fields)
        if unknown:
            raise ValidationError('Unknown field.', unknown)

    @post_dump(pass_many=False)
    def load_queried_nested_fields(self, data):
        """Injects nested fields requested in `include` into the JSON dump.

        Expects `include` in self.context, containing only valid values.

        """
        if 'include' not in self.context:
            return data
        include = self.context['include']
        for key, v in include.items():
            if key not in data or not data[key]:
                continue
            model = v['resource'].model
            if isinstance(data[key], list):
                primary_key = inspect(model).primary_key[0].name
                query = model.query.filter(getattr(model, primary_key).in_(data[key])).all()
                many = True
            else:
                query = model.query.get(data[key])
                many = False
            s = v['resource'].schema(many=many, only=v['only'])
            data[key] = s.dump(query).data

    @post_dump(pass_many=False)
    def add_language(self, data):
        """Add information about the languge of the output."""
        data['language'] = self.language
        return data

    @pre_load
    def set_language(self, data):
        """Let a language in data override the language for the schema instance."""
        self.language = data.pop('language', self.language)
        return data

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
        exclude = ['translation']


# Supermarket schemas

class Brand(CustomSchema):
    # id, name
    # refs: retailer, products, stores
    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='brands', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='brands', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='brands', _external=True),
        'related': {
            'retailer': HyperlinkRelated(
                'api.resourceitem', {'type': 'retailers'}, external=True, attribute='retailer'),
            'stores': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'stores'}, external=True, attribute='stores'),
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
        'self': ma.URLFor('api.resourceitem', type='categories', id='<id>', _external=True),
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
    category = Nested('CriterionCategory', only=('id', 'name', 'category'))
    improves_hotspots = Nested('CriterionImprovesHotspot', exclude=['criterion'], many=True)

    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='criteria', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='criteria', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='criteria', _external=True),
        'related': {
            'hotspots': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'hotspots'}, external=True,
                attribute='improves_hotspots', url_key=('hotspot_id', 'id'))
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Criterion


class CriterionCategory(CustomSchema):
    # id, name
    # refs: criteria, subcategories, category
    category = Nested('CriterionCategory', only=('id', 'name'))

    class Meta(CustomSchema.Meta):
        model = m.Criterion


class CriterionImprovesHotspot(CustomSchema):
    # primary key: criterion_id + hotspot_id
    # weight, explanation
    # refs: criterion, hotspot

    @property
    def schema_description(self):
        """Add related doc to schema description."""
        doc = super().schema_description
        doc['fields']['hotspot']['doc'] = url_for(
            'api.resourcedoc', type='hotspots', _external=True)
        return doc

    class Meta(CustomSchema.Meta):
        model = m.CriterionImprovesHotspot


class Hotspot(CustomSchema):
    # id, name, description
    # refs: scores

    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='hotspots', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='hotspots', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='hotspots', _external=True)
    })

    class Meta(CustomSchema.Meta):
        model = m.Hotspot


class Ingredient(CustomSchema):
    # primary key: product_id + weight
    # weight, name, percentage
    # refs: product, resource, origin, supplier

    @property
    def schema_description(self):
        """Add related doc to schema description."""
        doc = super().schema_description
        doc['fields']['resource']['doc'] = url_for(
            'api.resourcedoc', type='resources', _external=True)
        doc['fields']['origin']['doc'] = url_for(
            'api.resourcedoc', type='origins', _external=True)
        doc['fields']['supplier']['doc'] = url_for(
            'api.resourcedoc', type='suppliers', _external=True)
        return doc

    class Meta(CustomSchema.Meta):
        model = m.Ingredient


class Label(CustomSchema):
    # id, name, type (product, retailer), description, details (JSONB), logo
    # refs: meets_criteria, resources, products, retailers
    name = Translated(attribute='name')
    description = Translated(attribute='description')
    meets_criteria = Nested('LabelMeetsCriterion', exclude=['label'], many=True)
    hotspots = ma.Method('get_hotspots', dump_only=True)

    @post_load
    def make_instance(self, data):
        instance = super().make_instance(data)
        if not instance.translation:
            instance.translation = m.Translation()
        return instance

    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='labels', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='labels', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='labels', _external=True),
        'related': {
            'products': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'products'}, external=True, attribute='products'),
            'resources': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'resources'}, external=True, attribute='resources'),
            'retailers': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'retailers'}, external=True, attribute='retailers'),
            'criteria': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'criteria'}, external=True,
                attribute='meets_criteria', url_key=('criterion_id', 'id'))
        }
    })

    def get_hotspots(self, m):
        hotspots = set()
        for mc in m.meets_criteria:
            for ih in mc.criterion.improves_hotspots:
                hotspots.add(ih.hotspot)
        return [h.id for h in hotspots]

    @property
    def schema_description(self):
        """Replace method field in schema description."""
        doc = super().schema_description
        doc['fields']['hotspots']['type'] = 'related'
        doc['fields']['hotspots']['list'] = True
        return doc

    @post_dump
    def add_hotspots_link(self, data):
        if 'links' in data:
            hotspots_link = None
            if data['hotspots']:
                hotspots = {'id:in': ','.join(map(str, data['hotspots']))}
                hotspots_link = url_for(
                    'api.resourcelist', type='hotspots', _external=True, **hotspots)
            data['links']['related']['hotspots'] = hotspots_link
        return data

    class Meta(CustomSchema.Meta):
        model = m.Label


class LabelMeetsCriterion(CustomSchema):
    # primary key: label_id + criterion_id
    # score, explanation
    # refs: criterion, label

    @property
    def schema_description(self):
        """Add related doc to schema description."""
        doc = super().schema_description
        doc['fields']['criterion']['doc'] = url_for(
            'api.resourcedoc', type='criteria', _external=True)
        return doc

    class Meta(CustomSchema.Meta):
        model = m.LabelMeetsCriterion


class Origin(CustomSchema):
    # id, name, code
    # refs: ingredients, supplies
    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='origins', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='origins', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='origins', _external=True),
        'related': {
            'supplies': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'supplies'}, external=True, attribute='supplies'),
            'products': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'products'}, external=True, attribute='ingredients',
                url_key=('product_id', 'id'))
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Origin


class Producer(CustomSchema):
    # id, name
    # refs: products
    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='producers', id='<id>', _external=True),
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
    ingredients = Nested('Ingredient', exclude=['product'], many=True)

    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='products', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='products', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='products', _external=True),
        'related': {
            'brand': HyperlinkRelated(
                'api.resourceitem', {'type': 'brands'}, external=True, attribute='brand'),
            'category': HyperlinkRelated(
                'api.resourceitem', {'type': 'categories'}, external=True, attribute='category'),
            'producer': HyperlinkRelated(
                'api.resourceitem', {'type': 'producers'}, external=True, attribute='producer'),
            'labels': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'labels'}, external=True, attribute='labels'),
            'stores': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'stores'}, external=True, attribute='stores'),
            'origins': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'origins'}, external=True, attribute='ingredients',
                url_key=('origin_id', 'id')),
            'resources': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'resources'}, external=True, attribute='ingredients',
                url_key=('resource_id', 'id')),
            'suppliers': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'suppliers'}, external=True, attribute='ingredients',
                url_key=('supplier_id', 'id'))
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Product


class Resource(CustomSchema):
    # id, name
    # refs: ingredients, labels, supplies
    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='resources', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='resources', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='resources', _external=True),
        'related': {
            'labels': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'labels'}, external=True, attribute='labels'),
            'supplies': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'supplies'}, external=True, attribute='supplies',
                url_key='resource_id'),
            'products': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'products'}, external=True, attribute='ingredients',
                url_key=('product_id', 'id'))
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Resource


class Retailer(CustomSchema):
    # id, name
    # refs: meets_criteria, brands, stores, labels
    meets_criteria = Nested('RetailerMeetsCriterion', exclude=['retailer'], many=True)

    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='retailers', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='retailers', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='retailers', _external=True),
        'related': {
            'brands': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'brands'}, external=True, attribute='brands',
                url_key='retailer_id'),
            'stores': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'stores'}, external=True, attribute='stores',
                url_key='retailer_id'),
            'labels': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'labels'}, external=True, attribute='labels'),
            'criteria': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'criteria'}, external=True,
                attribute='meets_criteria', url_key=('criterion_id', 'id'))
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Retailer


class RetailerMeetsCriterion(CustomSchema):
    # primary key: retailer_id + criterion_id
    # satisfied, explanation
    # refs: criterion

    @property
    def schema_description(self):
        """Add related doc to schema description."""
        doc = super().schema_description
        doc['fields']['criterion']['doc'] = url_for(
            'api.resourcedoc', type='criteria', _external=True)
        return doc

    class Meta(CustomSchema.Meta):
        model = m.RetailerMeetsCriterion


class Score(CustomSchema):
    # primary key: hotspot_id, supply_id
    # score, explanation
    # refs: hotspot, supply

    @property
    def schema_description(self):
        """Add related doc to schema description."""
        doc = super().schema_description
        doc['fields']['hotspot']['doc'] = url_for(
            'api.resourcedoc', type='hotspots', _external=True)
        return doc

    class Meta(CustomSchema.Meta):
        model = m.Score


class Store(CustomSchema):
    # id, name
    # refs: retailer, brands, products
    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='stores', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='stores', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='stores', _external=True),
        'related': {
            'retailer': HyperlinkRelated(
                'api.resourceitem', {'type': 'retailers'}, external=True, attribute='retailer'),
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
        'self': ma.URLFor('api.resourceitem', type='suppliers', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='suppliers', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='suppliers', _external=True),
        'related': {
            'supplies': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'supplies'}, external=True, attribute='supplies',
                url_key='supplier_id'),
            'products': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'products'}, external=True, attribute='ingredients',
                url_key=('product_id', 'id'))
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Supplier


class Supply(CustomSchema):
    # id
    # refs: resource, origin, supplier, scores
    scores = Nested('Score', exclude=['supply'], many=True)

    links = Hyperlinks({
        'self': ma.URLFor('api.resourceitem', type='supplies', id='<id>', _external=True),
        'list': ma.URLFor('api.resourcelist', type='supplies', _external=True),
        'doc': ma.URLFor('api.resourcedoc', type='supplies', _external=True),
        'related': {
            'resource': HyperlinkRelated(
                'api.resourceitem', {'type': 'resources'}, external=True, attribute='resource'),
            'origin': HyperlinkRelated(
                'api.resourceitem', {'type': 'origins'}, external=True, attribute='origin'),
            'supplier': HyperlinkRelated(
                'api.resourceitem', {'type': 'suppliers'}, external=True, attribute='supplier'),
            'hotspots': HyperlinkRelatedList(
                'api.resourcelist', {'type': 'hotspots'}, external=True, attribute='scores',
                url_key=('hotspot_id', 'id'))
        }
    })

    class Meta(CustomSchema.Meta):
        model = m.Supply
