import json

from moflask.flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TypeDecorator


db = SQLAlchemy()


# custom data types

class Serialized(TypeDecorator):
    impl = db.Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


# helper tables

brands_stores = db.Table(
    'brands_stores',
    db.Column('brand_id', db.Integer, db.ForeignKey('brands.id'), primary_key=True),
    db.Column('store_id', db.Integer, db.ForeignKey('stores.id'), primary_key=True)
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
    __tablename__ = 'categories'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='category', lazy=True)


class Criterion(db.Model):
    __tablename__ = 'criteria'
    id = db.Column(db.Integer(), primary_key=True)
    type = db.Column(db.String(32))  # 'label' or 'retailer'
    code = db.Column(db.String(8))  # consortium identifier
    name = db.Column(db.String(64))
    details = db.Column(Serialized())  # details holds question, explanation
    improves_hotspots = db.relationship('CriterionImprovesHotspot', lazy=True)


class CriterionImprovesHotspot(db.Model):
    __tablename__ = 'criteria_hotspots'
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    hotspot_id = db.Column(db.ForeignKey('hotspots.id'), primary_key=True)
    weight = db.Column(db.Integer)
    explanation = db.Column(db.Text)
    hotspot = db.relationship('Hotspot', lazy=True)


class Hotspot(db.Model):
    __tablename__ = 'hotspots'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(256))
    description = db.Column(db.Text)
    # scores – backref from Score


class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    product_id = db.Column(db.ForeignKey('products.id'), primary_key=True)
    resource_id = db.Column(db.ForeignKey('resources.id'), primary_key=True)
    origin_id = db.Column(db.ForeignKey('origins.id'), nullable=True)
    supplier_id = db.Column(db.ForeignKey('suppliers.id'), nullable=True)
    product = db.relationship('Product', lazy=True, backref=db.backref('ingredients', lazy=True))
    resource = db.relationship('Resource', lazy=True, backref=db.backref('ingredients', lazy=True))
    origin = db.relationship('Origin', lazy=True, backref=db.backref('ingredients', lazy=True))
    supplier = db.relationship('Supplier', lazy=True, backref=db.backref('ingredients', lazy=True))
    percentage = db.Column(db.Integer)


class Label(db.Model):
    __tablename__ = 'labels'
    id = db.Column(db.Integer(), primary_key=True)
    type = db.Column(db.String(32))  # 'product' or 'retailer'
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    logo = db.Column(db.String(256))
    meets_criteria = db.relationship('LabelMeetsCriterion', lazy=True)
    # products – backref from Product
    # retailers – backref from Retailer


class LabelMeetsCriterion(db.Model):
    __tablename__ = 'labels_criteria'
    label_id = db.Column(db.ForeignKey('labels.id'), primary_key=True)
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    satisfied = db.Column(db.Boolean)
    explanation = db.Column(db.Text)
    criterion = db.relationship('Criterion', lazy=True)


class Origin(db.Model):
    __tablename__ = 'origins'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    # ingredients – backref from Ingredient
    # supplies – backref from Supply


class Producer(db.Model):
    __tablename__ = 'producers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='producer', lazy=True)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    details = db.Column(Serialized())  # holds image url, weight, price, currency
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
    # category – backref from Category
    # ingredients – backref from Ingredient
    # producer – backref from Producer


class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    # ingredients – backref from Ingredient
    # supplies – backref from Supply


class Retailer(db.Model):
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
    __tablename__ = 'retailer_criteria'
    retailer_id = db.Column(db.ForeignKey('retailers.id'), primary_key=True)
    criterion_id = db.Column(db.ForeignKey('criteria.id'), primary_key=True)
    satisfied = db.Column(db.Boolean)
    explanation = db.Column(db.Text)
    criterion = db.relationship('Criterion', lazy=True)


class Score(db.Model):
    __tablename__ = 'scores'
    hotspot_id = db.Column(db.ForeignKey('hotspots.id'), primary_key=True)
    supply_id = db.Column(db.ForeignKey('supplies.id'), primary_key=True)
    score = db.Column(db.Float, nullable=False)
    explanation = db.Column(db.Text)
    hotspot = db.relationship(
        'Hotspot', lazy=True, backref=db.backref('scores', lazy=True))
    supply = db.relationship(
        'Supply', lazy=True, backref=db.backref('scores', lazy=True))


class Store(db.Model):
    __tablename__ = 'stores'
    id = db.Column(db.Integer(), primary_key=True)
    retailer_id = db.Column(db.ForeignKey('retailers.id'))
    name = db.Column(db.String(64))
    # brands – backref from Brand
    # products – backref from Product
    # retailer – backref from Retailer


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    # ingredients – backref from Ingredient
    # supplies – backref from Supply


class Supply(db.Model):
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
