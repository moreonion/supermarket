from moflask.flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import CheckConstraint


db = SQLAlchemy()


class Translation(JSONB):

    """Translation type, contains a JSON of translated data."""

    pass


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
    name = db.Column(db.String(128))
    details = db.Column(JSONB)  # details holds question, measures
    improves_hotspots = db.relationship(
        'CriterionImprovesHotspot', backref=db.backref('criterion'))
    category_id = db.Column(db.ForeignKey('criterion_category.id'))
    # category – backref from CriterionCategory


class CriterionCategory(db.Model):

    """Category for criteria.

    Criteria are bundled in categories and those categories are grouped together
    in higher categories.

    """

    __tablename__ = 'criterion_category'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(128))
    parent_id = db.Column(db.ForeignKey('criterion_category.id'))
    subcategories = db.relationship(
        'CriterionCategory', backref=db.backref('category', remote_side=[id]))
    criteria = db.relationship(
        'Criterion', backref=db.backref('category'))
    # category – backref from CriterionCategory


class CriterionImprovesHotspot(db.Model):

    """Maps criteria to hotspots.

    Specifies in what way and with how much impact a criterion improves a certain hotspot score.

    """

    __tablename__ = 'criteria_hotspots'
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    hotspot_id = db.Column(db.ForeignKey('hotspots.id'), primary_key=True)
    weight = db.Column(db.SmallInteger)
    explanation = db.Column(db.Text)
    hotspot = db.relationship('Hotspot', lazy=True)
    # criterion – backref from Criterion


class Hotspot(db.Model):

    """A hotspot or issue is an area of concern (e.g. Climate Risk)."""

    __tablename__ = 'hotspots'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    # scores – backref from Score


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
    product = db.relationship('Product', lazy=True, backref=db.backref('ingredients', lazy=True))
    resource = db.relationship('Resource', lazy=True, backref=db.backref('ingredients', lazy=True))
    origin = db.relationship('Origin', lazy=True, backref=db.backref('ingredients', lazy=True))
    supplier = db.relationship('Supplier', lazy=True, backref=db.backref('ingredients', lazy=True))
    name = db.Column(db.String(256))
    percentage = db.Column(db.SmallInteger)


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
    details = db.Column(JSONB)  # Holds overall score
    logo = db.Column(db.String(256))
    meets_criteria = db.relationship('LabelMeetsCriterion', lazy=True)
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


class LabelCountry(db.Model):

    """Country where a label is in use, represented by its 2 letter ISO code."""

    __tablename__ = 'label_countries'
    code = db.Column(db.String(2), primary_key=True)
    # labels – backref from Label


class LabelMeetsCriterion(db.Model):

    """Maps labels to their criteria.

    Describes how well a label meets a certain criterion by assigning a score
    and an explanation.

    """

    __tablename__ = 'labels_criteria'
    label_id = db.Column(db.ForeignKey('labels.id'), primary_key=True)
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    score = db.Column(db.SmallInteger)
    explanation = db.Column(db.Text)
    criterion = db.relationship('Criterion')
    label = db.relationship('Label')


class Origin(db.Model):

    """The origin of a resource (a country or a FAO Major Fishing Area)."""

    __tablename__ = 'origins'
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(2))
    name = db.Column(db.String(64))
    # ingredients – backref from Ingredient
    # supplies – backref from Supply


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
    name = db.Column(db.String(64))
    details = db.Column(JSONB)  # holds image url, weight, price, currency
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


class Resource(db.Model):

    """A resource (“Rohstoff”), independent of its origin or use in products."""

    __tablename__ = 'resources'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    # ingredients – backref from Ingredient
    # labels – backref from Label
    # supplies – backref from Supply


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
    meets_criteria = db.relationship('RetailerMeetsCriterion', lazy=True)
    labels = db.relationship(
        'Label', secondary=retailers_labels,
        lazy='subquery', backref=db.backref('retailers', lazy=True)
    )


class RetailerMeetsCriterion(db.Model):

    """Maps retailer policies to their criteria.

    Describes how well a policy meets a certain criterion by assigning a score
    and an explanation.

    """

    __tablename__ = 'retailer_criteria'
    retailer_id = db.Column(db.ForeignKey('retailers.id'), primary_key=True)
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    satisfied = db.Column(db.Boolean)
    explanation = db.Column(db.Text)
    criterion = db.relationship('Criterion', lazy=True)


class Score(db.Model):

    """Maps the influence that a supply has on a hotspot area."""

    __tablename__ = 'scores'
    hotspot_id = db.Column(db.ForeignKey('hotspots.id'), primary_key=True)
    supply_id = db.Column(db.ForeignKey('supplies.id'), primary_key=True)
    score = db.Column(db.SmallInteger, nullable=False)
    explanation = db.Column(db.Text)
    hotspot = db.relationship(
        'Hotspot', lazy=True, backref=db.backref('scores', lazy=True))
    supply = db.relationship(
        'Supply', lazy=True, backref=db.backref('scores', lazy=True))


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
