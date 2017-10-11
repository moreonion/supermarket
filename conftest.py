import pytest

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
def example_data_products(request, app, db):
    with app.app_context():
        print('\n Setting up ingredients example data for {} {}'.format(id(db), db))
        p1 = m.Product(
            name={'en': 'Multilingual Product',
                  'de': 'Mehrsprachiges Produkt'},
            details={'en': 'A product of society',
                     'de': 'Ein Produkt der Gesellschaft'}
        )
        i1 = m.Ingredient(
            weight=1000,
            name={'en': 'Multilingual Ingredient',
                  'de': 'Mehrsprachige Ingredient'},
            product=p1)

        p2 = m.Product(
            name={'en': 'English Product'},
            details={'en': 'A product of English society'})
        i2 = m.Ingredient(
            weight=1000,
            name={'en': 'English Ingredient (probably Tea)'},
            product=p2)

        p3 = m.Product(
            name={'de': 'Deutsches Produkt'},
            details={'de': 'Faelscht Emissionsdaten'})
        i3 = m.Ingredient(
            weight=10000,
            name={'de': 'Deutscher Inhaltsstoff (wahrscheinlich Sauerkraut)'},
            product=p3)

        db.session.add_all([p1, i1, p2, i2, p3, i3])
        db.session.commit()


@pytest.fixture(scope='class')
def example_data_criteria(request, app, db):
    with app.app_context():
        print('\nSetting up criteria example data for {} {}'.format(id(db), db))
        c1 = m.Criterion(name={'en': 'Multilingual Criterion',
                               'de': 'Mehrsprachiges Criterion'},
                         details={'en': 'Multilingual details',
                                  'de': 'Mehrsprachige Details'})
        c2 = m.Criterion(name={'en': 'English Criterion'},
                         details={'en': 'English details'})
        c3 = m.Criterion(name={'de': 'Deutsches Criterion'},
                         details={'de': 'Deutsche Details'})

        cc1 = m.CriterionCategory(name={'en': 'Multilingual Criterion Category',
                                        'de': 'Mehrsprachige Criterion Category'})
        cc2 = m.CriterionCategory(name={'en': 'English Criterion Category'})
        cc3 = m.CriterionCategory(name={'de': 'Deutsche Criterion Category'})

        cc11 = m.CriterionCategory(name={'en': 'Turtle', 'de': 'Kroete'})

        cc1.subcategories = [cc11]

        cc1.criteria = [c1]
        cc2.criteria = [c2]
        cc3.criteria = [c3]

        db.session.add_all([c1, c2, c3, cc1, cc2, cc3, cc11])
        db.session.commit()


@pytest.fixture(scope='class')
def example_data_resources(request, app, db):
    with app.app_context():
        print('\nSetting up resource example data for {} {}'.format(id(db), db))
        r1 = m.Resource(name={'en': 'English Test Resource'})
        r2 = m.Resource(name={'de': 'Deutsche Test Resource'})
        r3 = m.Resource(name={'en': 'Multilingual Test Resource',
                              'de': 'Mehrsprachige Test Resource'})

        db.session.add_all([r1, r2, r3])
        db.session.commit()


@pytest.fixture(scope='class')
def example_data_hotspots(request, app, db):
    with app.app_context():
        print('\nSetting up hotspot example data for {} {}'.format(id(db), db))
        h1 = m.Hotspot(name={'en': 'Multilingual hotspot',
                             'de': 'Mehrsprachiger hotspot'},
                       description={
                           'en': 'This hotspot speaks 2 languages',
                           'de': 'Dieser hotspot spricht 2 sprachen'})
        h2 = m.Hotspot(name={'en': 'English hotspot'},
                       description={'en': 'This hotspot speaks English'})
        h3 = m.Hotspot(name={'de': 'Deutscher hotspot'},
                       description={'de': 'Dieser hotspot spricht deutsch'})

        db.session.add_all([h1, h2, h3])
        db.session.commit()


@pytest.fixture(scope='class')
def example_data_scores(request, app, db):
    with app.app_context():
        print('\nSetting up score example data for {} {}'.format(id(db), db))
        hotspot = m.Hotspot(name={'en': 'Test Hotspot'})
        resource = m.Resource(name={'en': 'Test Resource'})
        origin = m.Origin(name='Test Origin')
        supplier = m.Supplier(name='Test Supplier')
        supply = m.Supply(resource=resource, origin=origin, supplier=supplier)
        supply2 = m.Supply(resource=resource, origin=origin, supplier=supplier)
        supply3 = m.Supply(resource=resource, origin=origin, supplier=supplier)
        score = m.Score(hotspot=hotspot, supply=supply, score=10,
                        explanation={'en': 'This explanation is in English.'})
        score2 = m.Score(hotspot=hotspot, supply=supply2, score=9,
                         explanation={'de': 'Diese Erklaerung ist auf deutsch.'})
        score3 = m.Score(hotspot=hotspot, supply=supply3, score=100,
                         explanation={'en': 'This explanation is multilingual!',
                                      'de': 'Diese Erklaerung ist mehrsprachig!'})

        db.session.add_all([score, score2, score3])
        db.session.commit()


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
def example_data_label_guide(request, app, db):
    with app.app_context():
        print('\nSetting up example data for label guide use cases for {} {}'.format(
            id(db), db))

        l1 = m.Label(name={"en": "English and German",
                           "de": "Englisch und Deutsch"},
                     description={"en": "English description",
                                  "de": "Deutsche Beschreibung"},
                     logo={'en': 'english_logo.png',
                           'de': 'german_logo.png'})
        l2 = m.Label(name={"en": "English only"},
                     description={"en": "English description only"},
                     logo={'en': 'english_only_logo.png'})
        l3 = m.Label(name={"de": "Nur Deutsch"},
                     description={"de": "Nur eine deutsche Beschreibung"},
                     logo={'de': 'german_only_logo.png'})

        crit1 = m.Criterion(name='Multilingual')
        crit2 = m.Criterion(name='Understandable')
        crit3 = m.Criterion(name='Ignorant')

        l1_m_c1 = m.LabelMeetsCriterion(
            label=l1,
            criterion=crit1,
            explanation={"en": "The label is both English and German.",
                         "de": "Das Label ist sowohl Deutsch, als auch Englisch."},
            score=100
        )
        l2_m_c2 = m.LabelMeetsCriterion(
            label=l2,
            criterion=crit2,
            explanation={
                "en": "The label is at least in English, so a lot of people will understand it."
            },
            score=50
        )
        l3_m_c3 = m.LabelMeetsCriterion(
            label=l3,
            criterion=crit3,
            explanation={
                "de": "Alles nur Deutsch."
            },
            score=100
        )

        l1.meets_criteria = [l1_m_c1]
        l2.meets_criteria = [l2_m_c2]
        l3.meets_criteria = [l3_m_c3]

        db.session.add_all([l1, l2, l3])
        db.session.commit()


@pytest.fixture(scope='class')
def example_data_origin(request, app, db):
    with app.app_context():
        print('\nSetting up origin example data for {} {}'.format(id(db), db))
        o1 = m.Origin(
            code='AT',
            name={
                'en': 'Austria',
                'de': 'Oesterreich'
            })
        o2 = m.Origin(
            code='DE',
            name={'de': 'Deutschland'})
        o3 = m.Origin(
            code='GB',
            name={'en': 'Great Britain'})

        db.session.add_all([o1, o2, o3])
        db.session.commit()


@pytest.fixture(scope='class')
def example_data_labels(request, app, db):
    with app.app_context():
        print('\nSetting up label example data for {} {}'.format(id(db), db))
        r1 = m.Resource(name={'en': 'Testresource #1'})
        r2 = m.Resource(name={'en': 'Testresource #2'})
        lbl_country = m.LabelCountry(code='TL')
        hotspot = m.Hotspot(
            name={'en': 'Quality Assurance'},
            description={'en': 'To achieve a better world, we need good code.' +
                               'And good code needs good QA.'}
        )
        crit_hs = m.CriterionImprovesHotspot(
            weight=100,
            explanation={'en': 'What better QA than solid test data?'},
            hotspot=hotspot
        )
        crit = m.Criterion(
            type='label',
            name={'en': 'The test improvement criterion'},
            improves_hotspots=[crit_hs]
        )
        crit_cat = m.CriterionCategory(
            name={'en': 'Test Data'},
            criteria=[crit]
        )
        lbl = m.Label(
            name={'en': 'Testlabel'},
            type='product',
            description={'en': 'For exceptional testing.'},
            logo={'en': 'beautiful_logo.png',
                  'de': 'horrible_logo.png'},
            resources=[r1, r2],
            countries=[lbl_country],
        )
        lbl_criterion = m.LabelMeetsCriterion(
            label=lbl,
            criterion=crit,
            score=100,
            explanation={'en': 'Does the label improve testing for all of us?'}
        )

        db.session.add(lbl)
        db.session.add(lbl_criterion)
        db.session.add(crit_cat)
        db.session.commit()
