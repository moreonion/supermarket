import pytest

from supermarket import App
from supermarket.model import db as _db
from supermarket.model import Brand, Retailer, Product, Category


@pytest.fixture(scope='session')
def app():
    '''Return a test application'''
    return App('supermarket', env='Testing')


@pytest.fixture(scope='class')
def db(request, app):
    '''Return a class scoped test database.

    Tests that are not part of a class will get their own database.
    '''
    def setup():
        with app.app_context():
            print('\nSetup DB {} {}'.format(id(_db), _db))
            _db.create_all()

    def teardown():
        with app.app_context():
            print('\nTeardown DB {} {}'.format(id(_db), _db))
            _db.session.remove()
            _db.drop_all()

    setup()
    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope='class')
def example_data_brands(request, app, db):
    def setup():
        with app.app_context():
            print('\nSetting up testdata for {} {}'.format(id(db), db))
            retailer = Retailer(name='Rewe')
            category = Category(name='Cookies')
            p1 = Product(name='Chocolate chip cookies', category=category)
            p2 = Product(name='Triple chocolate bombs', category=category)
            brand = Brand(name='Clever', retailer=retailer, products=[p1])
            db.session.add(p2)
            db.session.add(brand)
            db.session.commit()

    setup()
