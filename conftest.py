import pytest

from supermarket import App
from supermarket.model import db as _db
from supermarket.model import Brand, Retailer, Product, Category
from supermarket.model import Resource, Label, LabelCountry, Criterion, LabelMeetsCriterion
from supermarket.model import Hotspot, CriterionImprovesHotspot, CriterionCategory


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
            print('\nSetting up brand example data for {} {}'.format(id(db), db))
            retailer = Retailer(name='Rewe')
            category = Category(name='Cookies')
            p1 = Product(name='Chocolate chip cookies', category=category)
            p2 = Product(name='Triple chocolate bombs', category=category)
            brand = Brand(name='Clever', retailer=retailer, products=[p1, p2])
            db.session.add(brand)
            db.session.commit()

    setup()


@pytest.fixture(scope='class')
def example_data_labels(request, app, db):
    def setup():
        with app.app_context():
            print('\nSetting up label example data for {} {}'.format(id(db), db))
            r1 = Resource(name='Testresource #1')
            r2 = Resource(name='Testresource #2')
            lbl_country = LabelCountry(code='TL')
            hotspot = Hotspot(
                name='Quality Assurance',
                description='To achieve a better world, we need good code.' +
                'And good code needs good QA.'
            )
            crit_hs = CriterionImprovesHotspot(
                weight=100,
                explanation='What better QA than solid test data?',
                hotspot=hotspot
            )
            crit = Criterion(
                type='label',
                name='The test improvement criterion',
                improves_hotspots=[crit_hs]
            )
            crit_cat = CriterionCategory(
                name='Test Data',
                criteria=[crit]
            )
            lbl = Label(
                name='Testlabel',
                type='product',
                description='For exceptional testing.',
                logo='beautiful_logo.png',
                resources=[r1, r2],
                countries=[lbl_country],
            )
            lbl_criterion = LabelMeetsCriterion(
                label=lbl,
                criterion=crit,
                score=100,
                explanation='Does the label improve testing for all of us?'
            )

            db.session.add(lbl)
            db.session.add(lbl_criterion)
            db.session.add(crit_cat)
            db.session.commit()

    setup()
