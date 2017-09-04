from moflask.flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import CheckConstraint


db = SQLAlchemy()


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
    """
    The brand of a product.
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
    """
    A category a product can be rated against.
    """
    __tablename__ = 'categories'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='category', lazy=True)


class Criterion(db.Model):
    """
    A criterion a label or a retailer can fulfill.
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
    """
    Specifies in what way and with how much impact a criterion improves a certain hotspot.
    """
    __tablename__ = 'criteria_hotspots'
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    hotspot_id = db.Column(db.ForeignKey('hotspots.id'), primary_key=True)
    weight = db.Column(db.SmallInteger)
    explanation = db.Column(db.Text)
    hotspot = db.relationship('Hotspot', lazy=True)
    # criterion – backref from Criterion


class Hotspot(db.Model):
    """
    A hotspot is an area of concern (e.g. Climate Risk).
    """
    __tablename__ = 'hotspots'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    # scores – backref from Score


class Ingredient(db.Model):
    """
    An ingredient of a product stemming from a certain resource.
    Contains information about the associated product, the weight of
    the ingredient, its origin, supplier and name. As well as the percentage
    of the product it takes up and the resource the ingredient stems from.
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
    """
    A label a product or a retailer can receive.
    Contains information about the type of the label (i.e. is it for products
    or is it for retailers), a description of the label and its logo.
    Additionally contains relationships to which criteria the label fulfills
    and in which countries the label is active.
    """
    __tablename__ = 'labels'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64), CheckConstraint('LENGTH(name)>0'), nullable=False, unique=True)
    type = db.Column(db.Enum('product', 'retailer', name='label_type'))
    description = db.Column(db.Text)
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
    """
    Maps labels to country codes.
    """
    __tablename__ = 'label_countries'
    code = db.Column(db.String(2), primary_key=True)
    # labels – backref from Label


class LabelMeetsCriterion(db.Model):
    """
    How well a label meets a certain criterion: this is defined by a score
    being assigned to a label for a certain criterion.
    """
    __tablename__ = 'labels_criteria'
    label_id = db.Column(db.ForeignKey('labels.id'), primary_key=True)
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    score = db.Column(db.SmallInteger)
    explanation = db.Column(db.Text)
    criterion = db.relationship('Criterion')
    label = db.relationship('Label')


class Origin(db.Model):
    """
    The origin of an ingredient, i.e. the country it stems from.
    """
    __tablename__ = 'origins'
    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(2))
    name = db.Column(db.String(64))
    # ingredients – backref from Ingredient
    # supplies – backref from Supply


class Producer(db.Model):
    """
    A producer producing certain products.
    """
    __tablename__ = 'producers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='producer', lazy=True)


class Product(db.Model):
    """
    Represents a product.
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
    """
    A resource an ingredient can stem from.
    """
    __tablename__ = 'resources'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    # ingredients – backref from Ingredient
    # labels – backref from Label
    # supplies – backref from Supply


class Retailer(db.Model):
    """
    Represents a retailer.
    Contains information about the retailer's name, associated brands and stores,
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
    """
    Whether or not a retailer fulfills a certain criterion.
    """
    __tablename__ = 'retailer_criteria'
    retailer_id = db.Column(db.ForeignKey('retailers.id'), primary_key=True)
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    satisfied = db.Column(db.Boolean)
    explanation = db.Column(db.Text)
    criterion = db.relationship('Criterion', lazy=True)


class Score(db.Model):
    """
    Supplies receive a score on how well they contribute to a hotspot area.
    """
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
    """
    A store belonging to a certain retailer.
    """
    __tablename__ = 'stores'
    id = db.Column(db.Integer(), primary_key=True)
    retailer_id = db.Column(db.ForeignKey('retailers.id'))
    name = db.Column(db.String(64))
    # brands – backref from Brand
    # products – backref from Product
    # retailer – backref from Retailer


class Supplier(db.Model):
    """
    A supplier of certain products.
    """
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    # ingredients – backref from Ingredient
    # supplies – backref from Supply


class Supply(db.Model):
    """
    The supply of a certain resource coming from a certain origin and/or
    supplier.
    """
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
