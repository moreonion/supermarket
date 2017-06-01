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
    criterion = m.Criterion(code='1.2.3', name='Saves the world')
    criterion.details = {
        'question': 'Does the certificate/label save the world?',
        'response_options': '0 - no, 1 - partly, 2 - totally!',
        'explanation': '2 applies only if it really saves the world.',
        'possible_scores': [-1, 0, 1, 2]  # -1 means not applicable
    }

    hotspot_assoc = m.CriterionImprovesHotspot(weight=2, explanation='Obvious.')
    hotspot_assoc.hotspot = m.Hotspot(name='Saving the world')
    criterion.improves_hotspots.append(hotspot_assoc)

    session.add(criterion)
    session.commit()

    assert criterion.id > 0
    assert criterion.details['possible_scores'][0] == -1
    assert len(criterion.improves_hotspots) == 1
    assert criterion.improves_hotspots[0].weight == 2
    assert criterion.improves_hotspots[0].explanation == 'Obvious.'
    assert criterion.improves_hotspots[0].hotspot.name == 'Saving the world'


def test_hotspot_model(session):
    hotspot = m.Hotspot(name='Saving the world', description='Today’s agenda')

    session.add(hotspot)
    session.commit()

    assert hotspot.id > 0


def test_label_model(session):
    label = m.Label(name='EU organic', description='A cool label.', logo='some url')

    criterion_1_assoc = m.LabelMeetsCriterion(satisfied=False, explanation='Nope.')
    criterion_1_assoc.criterion = m.Criterion(name='Saves the world')
    label.meets_criteria.append(criterion_1_assoc)

    criterion_2_assoc = m.LabelMeetsCriterion(satisfied=True, explanation='At least a few of us...')
    criterion_2_assoc.criterion = m.Criterion(name='Makes us all happy')
    label.meets_criteria.append(criterion_2_assoc)

    product = m.Product(name='Organic vegan gluten-free cookies')
    product.labels.append(label)

    session.add(label)
    session.commit()

    assert label.id > 0
    assert product.id > 0
    assert len(label.meets_criteria) == 2
    assert label.products[0].name == 'Organic vegan gluten-free cookies'
    assert label.meets_criteria[0].satisfied is False
    assert label.meets_criteria[0].explanation == 'Nope.'
    assert label.meets_criteria[0].criterion.name == 'Saves the world'


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
    raw_palm_oil = m.Resource(name='Palm oil')
    palm_oil = m.Ingredient(
        resource=raw_palm_oil,
        percentage=90
    )
    raw_cocoa = m.Resource(name='Cocoa')
    peru = m.Origin(name='Peru')
    supplier = m.Supplier(name='Cocoa Trade Inc.')
    cocoa = m.Ingredient(
        resource=raw_cocoa,
        origin=peru,
        supplier=supplier,
        percentage=10
    )
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
        ingredients=[palm_oil, cocoa],
        labels=[organic]
    )

    session.add(product)
    session.commit()

    assert product.id > 0
    assert organic.products[0] == product
    assert raw_palm_oil.ingredients[0].product == product
    assert raw_cocoa.ingredients[0].product == product # Read: Raw cocoa used as an ingredient
    assert raw_cocoa.ingredients[0].origin == peru
    assert raw_cocoa.ingredients[0].supplier == supplier
    assert raw_cocoa.ingredients[0].percentage == 10
    assert peru.ingredients[0].product == product      # Read: Ingredients from Peru
    assert supplier.ingredients[0].product == product  # Read: Ingredients from this supplier
    assert billa.products[0] == product
    assert brand.products[0] == product
    assert producer.products[0] == product
    assert category.products[0] == product


def test_retailer_model(session):
    retailer = m.Retailer(name='Rewe')
    m.Store(name='Billa', retailer=retailer)
    m.Store(name='Penny', retailer=retailer)
    m.Brand(name='Clever', retailer=retailer)
    m.Label(name='BEPI', type='retailer', retailers=[retailer])

    criterion_1_assoc = m.RetailerMeetsCriterion(satisfied=False, explanation='Nope.')
    criterion_1_assoc.criterion = m.Criterion(name='Saves the world', type='retailer')
    retailer.meets_criteria.append(criterion_1_assoc)

    criterion_2_assoc = m.RetailerMeetsCriterion(
        satisfied=True, explanation='At least a few of us...')
    criterion_2_assoc.criterion = m.Criterion(name='Makes us all happy', type='retailer')
    retailer.meets_criteria.append(criterion_2_assoc)

    session.add(retailer)
    session.commit()

    assert retailer.id > 0
    assert len(retailer.stores) == 2
    assert len(retailer.brands) == 1
    assert len(retailer.meets_criteria) == 2
    assert len(retailer.labels) == 1
    assert retailer.name == 'Rewe'
    assert retailer.meets_criteria[0].satisfied is False
    assert retailer.meets_criteria[0].explanation == 'Nope.'
    assert retailer.meets_criteria[0].criterion.name == 'Saves the world'
    assert retailer.meets_criteria[0].criterion.type == 'retailer'
    assert retailer.labels[0].name == 'BEPI'


def test_score_model(session):
    resource = m.Resource(name='pork fat')
    origin = m.Origin(name='austria')
    supplier = m.Supplier(name='huber-bauer')
    hotspot = m.Hotspot(name='animal rights')
    score = m.Score(
        resource=resource,
        origin=origin,
        supplier=supplier,
        hotspot=hotspot,
        score=3,
        explanation='foo'
    )

    session.add(score)
    session.commit()

    assert resource.scores[0].origin == origin
    assert resource.scores[0].supplier == supplier
    assert resource.scores[0].hotspot == hotspot
    assert origin.scores[0].resource == resource
    assert supplier.scores[0].resource == resource
    assert hotspot.scores[0].resource == resource


def test_store_model(session):
    retailer = m.Retailer(name='Rewe')
    store = m.Store(name='Billa', retailer=retailer)

    session.add(store)
    session.commit()

    assert store.id > 0
    assert store.retailer.id > 0
