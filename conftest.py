import pytest

from supermarket import App
from supermarket.model import db as _db


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
