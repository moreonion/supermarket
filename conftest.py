import pytest

from supermarket import App
from supermarket.model import db as _db


@pytest.fixture(scope='session')
def app():
    return App('supermarket', env='Testing')


@pytest.fixture(scope='session')
def db(app):
    '''Session-wide test database.'''
    with app.app_context():
        print('setup db')
        print(_db)
        print(id(_db))
        _db.create_all()
    yield _db
    with app.app_context():
        print('teardown db')
        print(_db)
        print(id(_db))
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def session(db, app):
    '''Creates a new database session for a test.'''
    connection = db.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    db.session = session
    yield session
    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture(scope='class')
def session_class(db, app):
    '''Creates a new database session for all tests of a class.'''
    connection = db.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    db.session = session
    yield session
    transaction.rollback()
    connection.close()
    session.remove()
