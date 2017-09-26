import pytest
import json

import supermarket.model as m
from supermarket import App


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
            print('\nSetup DB {} {}'.format(id(m.db), m.db))
            m.db.create_all()

    def teardown():
        with app.app_context():
            print('\nTeardown DB {} {}'.format(id(m.db), m.db))
            m.db.session.remove()
            m.db.drop_all()

    setup()
    request.addfinalizer(teardown)
    return m.db


@pytest.fixture(scope='class')
def example_data_brands(request, app, db):
    with app.app_context():
        print('\nSetting up brand example data for {} {}'.format(id(db), db))
        retailer = m.Retailer(name='Rewe')
        category = m.Category(name='Cookies')
        p1 = m.Product(name='Chocolate chip cookies', category=category)
        p2 = m.Product(name='Triple chocolate bombs', category=category)
        brand = m.Brand(name='Clever', retailer=retailer, products=[p1])
        db.session.add(p2)
        db.session.add(brand)
        db.session.commit()


@pytest.fixture(scope='class')
def example_data_criteria(request, app, db):
    with app.app_context():
        print('\nSetting up criteria example data for {} {}'.format(id(db), db))
        crit_en_only = m.Criterion(
            type='label',
            name='English only criterion',
            details=json.dumps({
                'question': [{'value': 'What is a question?',
                              'lang': 'en'}],
                'measures': {
                    2: [{'value': 'A phrase with an answer.',
                         'lang': 'en'}]
                }
            })
        )

        crit_de_only = m.Criterion(
            type='label',
            name='German only criterion',
            details=json.dumps({
                'question': [{'value': 'Was ist eine Frage?',
                             'lang': 'de'}],
                'measures': {
                    2: [{'value': 'Ein Satz mit einer Antwort.',
                         'lang': 'de'}]
                }
            })
        )

        crit_de_en = m.Criterion(
            type='label',
            name='German and English criterion',
            details=json.dumps({
                'question': [{'value': 'What is a question?',
                              'lang': 'en'},
                             {'value': 'Was ist eine Frage?',
                              'lang': 'de'}],
                'measures': {
                    2: [{'value': 'A phrase with an answer.',
                         'lang': 'en'},
                        {'value': 'Ein Satz mit einer Antwort.',
                         'lang': 'de'}]
                }
            })
        )

        db.session.add(crit_en_only)
        db.session.add(crit_de_only)
        db.session.add(crit_de_en)
        db.session.commit()


@pytest.fixture(scope='class')
def example_data_labels(request, app, db):
    with app.app_context():
        print('\nSetting up label example data for {} {}'.format(id(db), db))
        r1 = m.Resource(name='Testresource #1')
        r2 = m.Resource(name='Testresource #2')
        lbl_country = m.LabelCountry(code='TL')
        hotspot = m.Hotspot(
            name='Quality Assurance',
            description='To achieve a better world, we need good code.' +
            'And good code needs good QA.'
        )
        crit_hs = m.CriterionImprovesHotspot(
            weight=100,
            explanation='What better QA than solid test data?',
            hotspot=hotspot
        )
        crit = m.Criterion(
            type='label',
            name='The test improvement criterion',
            improves_hotspots=[crit_hs]
        )
        crit_cat = m.CriterionCategory(
            name='Test Data',
            criteria=[crit]
        )
        lbl = m.Label(
            name='Testlabel',
            type='product',
            description='For exceptional testing.',
            logo='beautiful_logo.png',
            resources=[r1, r2],
            countries=[lbl_country],
        )
        lbl_criterion = m.LabelMeetsCriterion(
            label=lbl,
            criterion=crit,
            score=100,
            explanation='Does the label improve testing for all of us?'
        )

        db.session.add(lbl)
        db.session.add(lbl_criterion)
        db.session.add(crit_cat)
        db.session.commit()
