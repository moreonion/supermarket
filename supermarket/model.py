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

products_resources = db.Table('products_resources',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('resource_id', db.Integer, db.ForeignKey('resources.id'), primary_key=True)
)

products_labels = db.Table('products_labels',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('label_id', db.Integer, db.ForeignKey('labels.id'), primary_key=True)
)

products_stores = db.Table('products_stores',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('store_id', db.Integer, db.ForeignKey('stores.id'), primary_key=True)
)

retailers_certificates = db.Table('retailers_certificates',
    db.Column('retailer_id', db.Integer, db.ForeignKey('retailers.id'), primary_key=True),
    db.Column('certificate_id', db.Integer, db.ForeignKey('certificates.id'), primary_key=True)
)


# main tables

class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    retailer_id = db.Column(db.Integer, db.ForeignKey('retailers.id'))
    products = db.relationship('Product', backref='brand', lazy=True)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='category', lazy=True)


class Certificate(db.Model):
    __tablename__ = 'certificates'
    id = db.Column(db.Integer(), primary_key=True)
    number = db.Column(db.String(8))
    name = db.Column(db.String(64))
    details = db.Column(Serialized()) # holds question, response options, explanation, possible scores


class CertificateMeetsCriterion(db.Model):
    __tablename__ = 'certificates_criteria'
    certificate_id = db.Column('certificate_id', db.Integer, db.ForeignKey('certificates.id'), primary_key=True)
    criterion_id = db.Column('criterion_id', db.Integer, db.ForeignKey('criteria.id'), primary_key=True)
    score = db.Column('score', db.Integer)
    explanation = db.Column('explanation', db.Text)
    criterion = db.relationship('Criterion', lazy=True)


class Criterion(db.Model):
    __tablename__ = 'criteria'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    hotspots = db.relationship('CriterionInfluencesHotspot', lazy=True)


class CriterionInfluencesHotspot(db.Model):
    __tablename__ = 'criteria_hotspots'
    criterion_id = db.Column('criterion_id', db.Integer, db.ForeignKey('criteria.id'), primary_key=True)
    hotspot_id = db.Column('hotspot_id', db.Integer, db.ForeignKey('hotspots.id'), primary_key=True)
    score = db.Column('score', db.Integer)
    explanation = db.Column('explanation', db.Text)
    hotspot = db.relationship('Hotspot', lazy=True)


class Hotspot(db.Model):
    __tablename__ = 'hotspots'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(256))
    description = db.Column(db.Text)


class Label(db.Model):
    __tablename__ = 'labels'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    logo = db.Column(db.String(256))
    criteria = db.relationship('LabelMeetsCriterion', lazy=True)


class LabelMeetsCriterion(db.Model):
    __tablename__ = 'labels_criteria'
    label_id = db.Column('label_id', db.Integer, db.ForeignKey('labels.id'), primary_key=True)
    criterion_id = db.Column('criterion_id', db.Integer, db.ForeignKey('criteria.id'), primary_key=True)
    score = db.Column('score', db.Integer)
    explanation = db.Column('explanation', db.Text)
    criterion = db.relationship('Criterion', lazy=True)


class Origin(db.Model):
    __tablename__ = 'origins'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))


class Producer(db.Model):
    __tablename__ = 'producers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='producer', lazy=True)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    producer_id = db.Column(db.Integer, db.ForeignKey('producers.id'))
    resources = db.relationship(
        'Resource', secondary=products_resources,
        lazy='subquery', backref=db.backref('products', lazy=True)
    )
    labels = db.relationship(
        'Label', secondary=products_labels,
        lazy='subquery', backref=db.backref('products', lazy=True)
    )
    stores = db.relationship(
        'Store', secondary=products_stores,
        lazy='subquery', backref=db.backref('products', lazy=True)
    )


class Store(db.Model):
    __tablename__ = 'stores'
    id = db.Column(db.Integer(), primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey('retailers.id'))
    name = db.Column(db.String(64))


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))


class Resource(db.Model):
    __tablename__ = 'resources'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))


class Retailer(db.Model):
    __tablename__ = 'retailers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    brands = db.relationship('Brand', backref='retailer', lazy=True)
    stores = db.relationship('Store', backref='retailer', lazy=True)
    certificates = db.relationship(
        'Certificate', secondary=retailers_certificates,
        lazy='subquery', backref=db.backref('retailers', lazy=True)
    )
