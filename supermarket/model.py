from moflask.flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


# helper tables

products_resources = db.Table(
    'products_resources',
    db.Column('product_id', db.Integer,
              db.ForeignKey('product.id'), primary_key=True),
    db.Column('resource_id', db.Integer,
              db.ForeignKey('resource.id'), primary_key=True)
)


# main tables

class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='brand', lazy=True)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='category', lazy=True)


class Hotspot(db.Model):
    __tablename__ = 'Hotspots'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))


class Label(db.Model):
    __tablename__ = 'labels'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))


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
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    producer_id = db.Column(db.Integer, db.ForeignKey('producer.id'))
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'))
    resources = db.relationship(
        'Resource', secondary=products_resources,
        lazy='subquery', backref=db.backref('products', lazy=True)
    )


class Store(db.Model):
    __tablename__ = 'stores'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64))
    products = db.relationship('Product', backref='store', lazy=True)


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
