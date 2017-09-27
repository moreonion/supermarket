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
        t = m.Translation()
        name = m.TranslatedString(value='English only criterion', language='en',
                                  translation=t, field='name')
        crit_en_only = m.Criterion(
            type='label',
            translation=t,
            name=[name],
            details=json.dumps({
                'question': [{'value': 'What is a question?',
                              'lang': 'en'}],
                'measures': {
                    2: [{'value': 'A phrase with an answer.',
                         'lang': 'en'}]
                }
            })
        )

        t = m.Translation()
        name = m.TranslatedString(value='German only criterion', language='de',
                                  translation=t, field='name')
        crit_de_only = m.Criterion(
            type='label',
            translation=t,
            name=[name],
            details=json.dumps({
                'question': [{'value': 'Was ist eine Frage?',
                             'lang': 'de'}],
                'measures': {
                    2: [{'value': 'Ein Satz mit einer Antwort.',
                         'lang': 'de'}]
                }
            })
        )

        t = m.Translation()
        name = m.TranslatedString(value='German and English criterion', language='en',
                                  translation=t, field='name')
        name_de = m.TranslatedString(value='Deutsch und Englisch Kriterium',
                                     language='de', translation=t, field='name')
        crit_de_en = m.Criterion(
            type='label',
            translation=t,
            name=[name, name_de],
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
        t = m.Translation()
        exp = m.TranslatedText(value='What better QA than solid test data?',
                               language='en', field='explanation',
                               translation=t)
        crit_hs = m.CriterionImprovesHotspot(
            weight=100,
            translation=t,
            explanation=[exp],
            hotspot=hotspot
        )
        t = m.Translation()
        name = m.TranslatedString(value='The test improvement criterion',
                                  language='en', field='name', translation=t)
        crit = m.Criterion(
            type='label',
            name=[name],
            translation=t,
            improves_hotspots=[crit_hs]
        )
        crit_cat = m.CriterionCategory(
            name='Test Data',
            criteria=[crit]
        )
        t = m.Translation()
        name = m.TranslatedString(value='Testlabel',
                                  language='en', field='name', translation=t)
        name_de = m.TranslatedString(value='Testerfuellung',
                                     language='de', field='name', translation=t)
        description = m.TranslatedText(value='For exceptional testing.',
                                       language='en', field='description',
                                       translation=t)
        description_de = m.TranslatedText(value='Fuer grossartiges Testen.',
                                          language='de', field='description',
                                          translation=t)
        lbl = m.Label(
            translation=t,
            name=[name, name_de],
            type='product',
            description=[description, description_de],
            logo='beautiful_logo.png',
            resources=[r1, r2],
            countries=[lbl_country],
        )

        t = m.Translation()
        name = m.TranslatedString(value='English Name', language='en',
                                  field='name', translation=t)
        name_de = m.TranslatedString(value='German Name', language='de',
                                     field='name', translation=t)
        description = m.TranslatedText(value='Only English description.',
                                       language='en', field='description',
                                       translation=t)
        lbl2 = m.Label(
            translation=t,
            name=[name, name_de],
            type='product',
            description=[description],
            logo='beautiful_logo.png',
            resources=[r1, r2],
            countries=[lbl_country],
        )

        t = m.Translation()
        explanation = m.TranslatedText(
            value='Does the label improve testing for all of us?',
            language='en', field='explanation', translation=t)
        explanation_de = m.TranslatedText(
            value='Verbessert das Label testen fuer alle?',
            language='de', field='explanation', translation=t)

        lbl_criterion = m.LabelMeetsCriterion(
            label=lbl,
            criterion=crit,
            score=100,
            translation=t,
            explanation=[explanation, explanation_de]
        )

        db.session.add(lbl)
        db.session.add(lbl2)
        db.session.add(lbl_criterion)
        db.session.add(crit_cat)
        db.session.commit()
