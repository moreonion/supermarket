import supermarket.model as m


def test_brand_model(session):
    retailer = m.Retailer(name='Rewe')
    store = m.Store(name='Billa')
    brand = m.Brand(name="Clever", retailer=retailer, stores=[store])

    session.add(brand)
    session.commit()

    assert brand.id > 0
    assert retailer.id > 0
    assert store.id > 0
    assert brand.retailer.name == 'Rewe'
    assert brand.stores[0].name == 'Billa'
    assert len(retailer.brands) == 1
    assert len(store.brands) == 1
    assert retailer.brands[0].name == 'Clever'
    assert store.brands[0].name == 'Clever'


def test_category_model(session):
    category = m.Category(name='cookies')
    product_1 = m.Product(name='Chocolate chip cookies', category=category)
    product_2 = m.Product(name='Triple chocolate bombs', category=category)

    session.add(product_1)
    session.add(product_2)
    session.commit()

    assert category.id > 0
    assert len(category.products) == 2
    assert product_1.category.name == 'cookies'


def test_criterion_model(session):
    criterion = m.Criterion(number='1.2.3', name='Saves the world')
    criterion.details = {
        'question': 'Does the certificate/label save the world?',
        'response_options': '0 - no, 1 - partly, 2 - totally!',
        'explanation': '2 applies only if it really saves the world.',
        'possible_scores': [-1, 0, 1, 2]  # -1 means not applicable
    }

    hotspot_assoc = m.CriterionImprovesHotspot(weight=2, explanation='Obvious.')
    hotspot_assoc.hotspot = m.Hotspot(name='Saving the world')
    criterion.hotspots.append(hotspot_assoc)

    session.add(criterion)
    session.commit()

    assert criterion.id > 0
    assert criterion.details['possible_scores'][0] == -1
    assert len(criterion.hotspots) == 1
    assert criterion.hotspots[0].weight == 2
    assert criterion.hotspots[0].explanation == 'Obvious.'
    assert criterion.hotspots[0].hotspot.name == 'Saving the world'


def test_hotspot_model(session):
    hotspot = m.Hotspot(name='Saving the world', description='Today’s agenda')

    session.add(hotspot)
    session.commit()

    assert hotspot.id > 0


def test_label_model(session):
    label = m.Label(name='EU organic', description='A cool label.', logo='some url')

    criterion_1_assoc = m.LabelMeetsCriterion(satisfied=False, explanation='Nope.')
    criterion_1_assoc.criterion = m.Criterion(name='Saves the world')
    label.criteria.append(criterion_1_assoc)

    criterion_2_assoc = m.LabelMeetsCriterion(satisfied=True, explanation='At least a few of us...')
    criterion_2_assoc.criterion = m.Criterion(name='Makes us all happy')
    label.criteria.append(criterion_2_assoc)

    product = m.Product(name='Organic vegan gluten-free cookies')
    product.labels.append(label)

    session.add(label)
    session.commit()

    assert label.id > 0
    assert product.id > 0
    assert len(label.criteria) == 2
    assert label.products[0].name == 'Organic vegan gluten-free cookies'
    assert label.criteria[0].satisfied is False
    assert label.criteria[0].explanation == 'Nope.'
    assert label.criteria[0].criterion.name == 'Saves the world'


def test_origin_model(session):
    origin = m.Origin(name='Indonesia')

    session.add(origin)
    session.commit()

    assert origin.id > 0


def test_producer_model(session):
    producer = m.Producer(name='Willy Wonka’s Chocolate Factory')
    product = m.Product(name='Zucchini Chocolate', producer=producer)

    session.add(product)
    session.commit()

    assert producer.id > 0
    assert producer.products[0] == product
    assert product.producer == producer


def test_product_model(session):
    palm_oil = m.Resource(name='Palm oil')
    cocoa = m.Resource(name='Cocoa')
    organic = m.Label(name='EU organic')
    billa = m.Store(name='Billa')
    brand = m.Brand(name='BestBio')
    producer = m.Producer(name='Raw Organic Cookie Factory')
    category = m.Category(name='Cookies')

    product = m.Product(
        name='Raw organic vegan gluten-free cookies',
        gtin='99999999999999',
        stores=[billa],
        brand=brand,
        producer=producer,
        category=category,
        details={
            'image': 'some url',
            'weight': '300 g',
            'price': '2,99',
            'currency': 'Euro'
        },
        resources=[palm_oil, cocoa],
        labels=[organic]
    )

    session.add(product)
    session.commit()

    assert product.id > 0
    assert organic.products[0] == product
    assert palm_oil.products[0] == product
    assert cocoa.products[0] == product
    assert billa.products[0] == product
    assert brand.products[0] == product
    assert producer.products[0] == product
    assert category.products[0] == product


def test_resource_model(session):
    resource = m.Resource(name='pork fat')
    # TODO: association with origins, hotspots, certificates, suppliers via model
    # with score and description

    assert 0


def test_retailer_model(session):
    retailer = m.Retailer(name='Rewe')
    m.Store(name='Billa', retailer=retailer)
    m.Store(name='Penny', retailer=retailer)
    m.Brand(name='Clever', retailer=retailer)

    criterion_1_assoc = m.RetailerMeetsCriterion(satisfied=False, explanation='Nope.')
    criterion_1_assoc.criterion = m.Criterion(name='Saves the world')
    retailer.criteria.append(criterion_1_assoc)

    criterion_2_assoc = m.RetailerMeetsCriterion(
        satisfied=True, explanation='At least a few of us...')
    criterion_2_assoc.criterion = m.Criterion(name='Makes us all happy')
    retailer.criteria.append(criterion_2_assoc)

    session.add(retailer)
    session.commit()

    assert retailer.id > 0
    assert len(retailer.stores) == 2
    assert len(retailer.brands) == 1
    assert len(retailer.criteria) == 2
    assert retailer.name == 'Rewe'
    assert retailer.criteria[0].satisfied is False
    assert retailer.criteria[0].explanation == 'Nope.'
    assert retailer.criteria[0].criterion.name == 'Saves the world'


def test_store_model(session):
    retailer = m.Retailer(name='Rewe')
    store = m.Store(name='Billa', retailer=retailer)

    session.add(store)
    session.commit()

    assert store.id > 0
    assert store.retailer.id > 0
