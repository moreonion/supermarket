from moflask.flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates
from marshmallow import ValidationError


db = SQLAlchemy()


class Translation(JSONB):

    """Translation type, contains a JSON of translated data."""

    @classmethod
    def validate_translation(cls, key, value):
        if not isinstance(value, dict):
            raise ValidationError('No language specified.', key)
        return value


# helper tables

brands_stores = db.Table(
    'brands_stores',
    db.Column('brand_id', db.Integer, db.ForeignKey('brands.id'), primary_key=True),
    db.Column('store_id', db.Integer, db.ForeignKey('stores.id'), primary_key=True)
)

labels_resources = db.Table(
    'labels_resources',
    db.Column('label_id', db.Integer, db.ForeignKey('labels.id'), primary_key=True),
    db.Column('resource_id', db.Integer, db.ForeignKey('resources.id'), primary_key=True)
)

labels_countries = db.Table(
    'labels_countries',
    db.Column('label_id', db.Integer, db.ForeignKey('labels.id'), primary_key=True),
    db.Column('country_code', db.String, db.ForeignKey('label_countries.code'), primary_key=True)
)

products_labels = db.Table(
    'products_labels',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('label_id', db.Integer, db.ForeignKey('labels.id'), primary_key=True)
)

products_stores = db.Table(
    'products_stores',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('store_id', db.Integer, db.ForeignKey('stores.id'), primary_key=True)
)

retailers_labels = db.Table(
    'retailers_labels',
    db.Column('retailer_id', db.Integer, db.ForeignKey('retailers.id'), primary_key=True),
    db.Column('label_id', db.Integer, db.ForeignKey('labels.id'), primary_key=True)
)

measures_labels = db.Table(
    'measures_labels',
    db.Column('label_id', db.Integer, db.ForeignKey('labels.id'), primary_key=True),
    db.Column('criterion_id', db.Integer, primary_key=True),
    db.Column('score', db.Integer),
    db.ForeignKeyConstraint(['criterion_id', 'score'], ['measures.criterion_id', 'measures.score'])
)

measures_retailers = db.Table(
    'measures_retailers',
    db.Column('retailer_id', db.Integer, db.ForeignKey('retailers.id'), primary_key=True),
    db.Column('criterion_id', db.Integer, primary_key=True),
    db.Column('score', db.Integer),
    db.ForeignKeyConstraint(['criterion_id', 'score'], ['measures.criterion_id', 'measures.score'])
)


# main tables

class Brand(db.Model):

    """The brand of a product.

    Contains information about the brands name, the retailer, the products that are part of
    this brand and the stores where those products are sold.

    """

    __tablename__ = 'brands'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    retailer_id = db.Column(db.ForeignKey('retailers.id'))
    products = db.relationship('Product', backref='brand', lazy=True)
    stores = db.relationship(
        'Store', secondary=brands_stores,
        lazy='subquery', backref=db.backref('brands', lazy=True)
    )
    # retailer – backref from Retailer


class Category(db.Model):

    """A category a product belongs to.

    Looking into using GS1 standards for food and beverages.

    """

    __tablename__ = 'categories'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='category', lazy=True)


class Criterion(db.Model):

    """A criterion a label or a retailer policy can fulfill.

    Criteria are bundled in categories and specify which measures need to be taken
    to improve the overall rating by a certain score.

    """

    __tablename__ = 'criteria'
    id = db.Column(db.Integer(), primary_key=True)
    type = db.Column(db.Enum('label', 'retailer', name='criterion_type'))
    name = db.Column(Translation)
    question = db.Column(Translation)
    improves_hotspots = db.relationship(
        'CriterionImprovesHotspot', backref=db.backref('criterion'))
    category_id = db.Column(db.ForeignKey('criterion_category.id'))
    # category – backref from CriterionCategory
    # measures – backref from Measure

    @validates('name', 'question')
    def validate(self, key, value):
        if key == 'name' and len(value) > 128:
            raise ValidationError('Only 128 characters allowed.', key)
        return Translation.validate_translation(key, value)

    def get_max_score(self):
        return max([m.score for m in self.measures])

    def get_label_score(self, label):
        for m in self.measures:
            if label in m.labels:
                return m.score
        return 0


class CriterionCategory(db.Model):

    """Category for criteria.

    Criteria are bundled in categories and those categories are grouped together
    in higher categories.

    """

    __tablename__ = 'criterion_category'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(Translation)
    parent_id = db.Column(db.ForeignKey('criterion_category.id'))
    subcategories = db.relationship(
        'CriterionCategory', backref=db.backref('category', remote_side=[id]))
    criteria = db.relationship(
        'Criterion', backref=db.backref('category'))
    # category – backref from CriterionCategory

    @validates('name')
    def validate(self, key, value):
        if key == 'name' and len(value) > 128:
            raise ValidationError('Only 128 characters allowed.', key)
        return Translation.validate_translation(key, value)

    def get_max_score(self):
        score = 0
        # for criteria add all max points
        for c in self.criteria:
            score += c.get_max_score()
        # for subcategories add 100% each
        for sc in self.subcategories:
            if 'Co-Labeling' not in sc.name['en']:  # co-labeling doesn’t count
                score += 100
        return score

    def get_label_score(self, label):
        label_score = 0
        for c in self.criteria:
            label_score += c.get_label_score(label)
        for sc in self.subcategories:
            label_score += sc.get_label_score(label)
        return round(100*label_score/self.get_max_score())


class CriterionImprovesHotspot(db.Model):

    """Maps criteria to hotspots.

    Specifies in what way and with how much impact a criterion improves a certain hotspot score.

    """

    __tablename__ = 'criteria_hotspots'
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    hotspot_id = db.Column(db.ForeignKey('hotspots.id'), primary_key=True)
    weight = db.Column(db.SmallInteger)
    explanation = db.Column(Translation)
    hotspot = db.relationship('Hotspot', lazy=True)
    # criterion – backref from Criterion

    @validates('explanation')
    def validate(self, key, value):
        return Translation.validate_translation(key, value)


class Hotspot(db.Model):

    """A hotspot or issue is an area of concern (e.g. Climate Risk)."""

    __tablename__ = 'hotspots'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(Translation)
    description = db.Column(Translation)
    # scores – backref from Score

    @validates('name', 'description')
    def validate(self, key, value):
        return Translation.validate_translation(key, value)


class Ingredient(db.Model):

    """An ingredient of a product.

    Contains information about the resource the ingredient stems from, its origin or supplier
    if known, and the order (weight) of items on the product’s ingredients list.

    """

    __tablename__ = 'ingredients'
    product_id = db.Column(db.ForeignKey('products.id'), primary_key=True)
    weight = db.Column(db.Integer(), primary_key=True)
    resource_id = db.Column(db.ForeignKey('resources.id'), nullable=True)
    origin_id = db.Column(db.ForeignKey('origins.id'), nullable=True)
    supplier_id = db.Column(db.ForeignKey('suppliers.id'), nullable=True)
    product = db.relationship('Product', lazy=True, backref=db.backref(
        'ingredients', lazy=True, cascade='all, delete-orphan'))
    resource = db.relationship('Resource', lazy=True, backref=db.backref('ingredients', lazy=True))
    origin = db.relationship('Origin', lazy=True, backref=db.backref('ingredients', lazy=True))
    supplier = db.relationship('Supplier', lazy=True, backref=db.backref('ingredients', lazy=True))
    name = db.Column(Translation)
    percentage = db.Column(db.SmallInteger)

    @validates('name')
    def validate(self, key, value):
        return Translation.validate_translation(key, value)


class Label(db.Model):

    """A label ensures that a product or retailer fulfills certain criteria.

    Contains information about the type of the label (i.e. is it for products
    or is it for retailers), a description and logo, the countries where
    it is in use and the criteria that have to be complied to.

    """

    __tablename__ = 'labels'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(Translation, nullable=False, unique=True)
    type = db.Column(db.Enum('product', 'retailer', name='label_type'))
    description = db.Column(Translation)
    logo = db.Column(Translation)
    meets_criteria = db.relationship(
        'Measure', secondary=measures_labels,
        lazy='subquery', backref=db.backref('labels', lazy=True)
    )
    resources = db.relationship(
        'Resource', secondary=labels_resources,
        lazy='subquery', backref=db.backref('labels', lazy=True)
    )
    countries = db.relationship(
        'LabelCountry', secondary=labels_countries,
        lazy='subquery', backref=db.backref('labels', lazy=True)
    )
    # products – backref from Product
    # retailers – backref from Retailer

    @validates('name', 'logo')
    def validate(self, key, value):
        if key == 'logo' and len(value) > 256:
            raise ValidationError('Only 256 characters allowed.', key)
        return Translation.validate_translation(key, value)


class LabelCountry(db.Model):

    """Country where a label is in use, represented by its 2 letter ISO code."""

    __tablename__ = 'label_countries'
    code = db.Column(db.String(2), primary_key=True)
    # labels – backref from Label


class Measure(db.Model):

    """Measures that can be inforced by a label or retailer to fullfill criteria.

    The score indicates how well the measure is fitting to fullfill its criterion.
    A label or retailer can only inforce one measure of the same criterion.

    """

    __tablename__ = 'measures'
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    score = db.Column(db.Integer(), primary_key=True)
    explanation = db.Column(Translation)
    criterion = db.relationship('Criterion', lazy=True, backref=db.backref(
        'measures', lazy=True, cascade='all, delete-orphan'))
    # labels – backref from Label
    # retailers – backref from Retailer

    @validates('explanation')
    def validate(self, key, value):
        return Translation.validate_translation(key, value)


class Origin(db.Model):

    """The origin of a resource (a country or a FAO Major Fishing Area)."""

    __tablename__ = 'origins'
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(2))
    name = db.Column(Translation)
    # ingredients – backref from Ingredient
    # supplies – backref from Supply

    @validates('name')
    def validate(self, key, value):
        if key == 'name' and len(value) > 64:
            raise ValidationError('Only 64 characters allowed.', key)
        return Translation.validate_translation(key, value)


class Producer(db.Model):

    """A producer producing certain products."""

    __tablename__ = 'producers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='producer', lazy=True)


class Product(db.Model):

    """Represents a product.

    Contains information about the product name, details (image, weight, ...), its Global Trade
    Item Number, the brand it belongs to, which category it falls in and the responsible producer.
    Also the labels the product received and the stores that it is sold in.

    """

    __tablename__ = 'products'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(Translation)
    details = db.Column(Translation)  # holds image url, weight, price, currency
    gtin = db.Column(db.String(14))   # Global Trade Item Number
    brand_id = db.Column(db.ForeignKey('brands.id'))
    category_id = db.Column(db.ForeignKey('categories.id'))
    producer_id = db.Column(db.ForeignKey('producers.id'))
    labels = db.relationship(
        'Label', secondary=products_labels,
        lazy='subquery', backref=db.backref('products', lazy=True)
    )
    stores = db.relationship(
        'Store', secondary=products_stores,
        lazy='subquery', backref=db.backref('products', lazy=True)
    )
    # brand – backref from Brand
    # category – backref from Category
    # ingredients – backref from Ingredient
    # producer – backref from Producer

    @validates('name', 'details')
    def validate(self, key, value):
        return Translation.validate_translation(key, value)


class Resource(db.Model):

    """A resource (“Rohstoff”), independent of its origin or use in products."""

    __tablename__ = 'resources'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(Translation)
    # ingredients – backref from Ingredient
    # labels – backref from Label
    # supplies – backref from Supply

    @validates('name')
    def validate(self, key, value):
        if key == 'name' and len(value) > 64:
            raise ValidationError('Only 64 characters allowed.', key)
        return Translation.validate_translation(key, value)


class Retailer(db.Model):

    """Represents a retailer.

    Contains information about the retailer’s name, associated brands and stores,
    whether the retailer fulfills certain criteria and the labels the retailer
    received.

    """

    __tablename__ = 'retailers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    brands = db.relationship('Brand', backref='retailer', lazy=True)
    stores = db.relationship('Store', backref='retailer', lazy=True)
    meets_criteria = db.relationship(
        'Measure', secondary=measures_retailers,
        lazy='subquery', backref=db.backref('retailers', lazy=True)
    )
    labels = db.relationship(
        'Label', secondary=retailers_labels,
        lazy='subquery', backref=db.backref('retailers', lazy=True)
    )


class Score(db.Model):

    """Maps the influence that a supply has on a hotspot area."""

    __tablename__ = 'scores'
    hotspot_id = db.Column(db.ForeignKey('hotspots.id'), primary_key=True)
    supply_id = db.Column(db.ForeignKey('supplies.id'), primary_key=True)
    score = db.Column(db.SmallInteger, nullable=False)
    explanation = db.Column(Translation)
    hotspot = db.relationship(
        'Hotspot', lazy=True, backref=db.backref('scores', lazy=True))
    supply = db.relationship(
        'Supply', lazy=True, backref=db.backref('scores', lazy=True, cascade='all, delete-orphan'))

    @validates('explanation')
    def validate(self, key, value):
        return Translation.validate_translation(key, value)


class Store(db.Model):

    """A store belonging to a certain retailer."""

    __tablename__ = 'stores'
    id = db.Column(db.Integer(), primary_key=True)
    retailer_id = db.Column(db.ForeignKey('retailers.id'))
    name = db.Column(db.String(64))
    # brands – backref from Brand
    # products – backref from Product
    # retailer – backref from Retailer


class Supplier(db.Model):

    """A supplier of a resource."""

    __tablename__ = 'suppliers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    # ingredients – backref from Ingredient
    # supplies – backref from Supply


class Supply(db.Model):

    """A resource coming from an origin or supplier."""

    __tablename__ = 'supplies'
    id = db.Column(db.Integer(), primary_key=True)
    resource_id = db.Column(db.ForeignKey('resources.id'))
    origin_id = db.Column(db.ForeignKey('origins.id'), nullable=True)
    supplier_id = db.Column(db.ForeignKey('suppliers.id'), nullable=True)
    resource = db.relationship(
        'Resource', lazy=True, backref=db.backref('supplies', lazy=True))
    origin = db.relationship(
        'Origin', lazy=True, backref=db.backref('supplies', lazy=True))
    supplier = db.relationship(
        'Supplier', lazy=True, backref=db.backref('supplies', lazy=True))
    # scores – backref from Score
