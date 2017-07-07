import supermarket.model as m


def test_brand_model(db):
    retailer = m.Retailer(name='Rewe')
    store = m.Store(name='Billa')
    brand = m.Brand(name="Clever", retailer=retailer, stores=[store])

    db.session.add(brand)
    db.session.commit()

    assert brand.id > 0
    assert retailer.id > 0
    assert store.id > 0
    assert brand.retailer.name == 'Rewe'
    assert brand.stores[0].name == 'Billa'
    assert len(retailer.brands) == 1
    assert len(store.brands) == 1
    assert retailer.brands[0].name == 'Clever'
    assert store.brands[0].name == 'Clever'


def test_category_model(db):
    category = m.Category(name='cookies')
    product_1 = m.Product(name='Chocolate chip cookies', category=category)
    product_2 = m.Product(name='Triple chocolate bombs', category=category)

    db.session.add(product_1)
    db.session.add(product_2)
    db.session.commit()

    assert category.id > 0
    assert len(category.products) == 2
    assert product_1.category.name == 'cookies'


def test_criterion_model(db):
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

    db.session.add(criterion)
    db.session.commit()

    assert criterion.id > 0
    assert criterion.details['possible_scores'][0] == -1
    assert len(criterion.improves_hotspots) == 1
    assert criterion.improves_hotspots[0].weight == 2
    assert criterion.improves_hotspots[0].explanation == 'Obvious.'
    assert criterion.improves_hotspots[0].hotspot.name == 'Saving the world'


def test_hotspot_model(db):
    hotspot = m.Hotspot(name='Saving the world', description='Today’s agenda')

    db.session.add(hotspot)
    db.session.commit()

    assert hotspot.id > 0


def test_label_model(db):
    label = m.Label(name='EU organic', description='A cool label.', logo='some url')

    criterion_1_assoc = m.LabelMeetsCriterion(satisfied=False, explanation='Nope.')
    criterion_1_assoc.criterion = m.Criterion(name='Saves the world')
    label.meets_criteria.append(criterion_1_assoc)

    criterion_2_assoc = m.LabelMeetsCriterion(satisfied=True, explanation='At least a few of us…')
    criterion_2_assoc.criterion = m.Criterion(name='Makes us all happy')
    label.meets_criteria.append(criterion_2_assoc)

    resource_1 = m.Resource(name='cocoa')
    resource_2 = m.Resource(name='palm oil')
    label.resources = [resource_1, resource_2]

    product = m.Product(name='Organic vegan gluten-free cookies')
    label.products.append(product)

    db.session.add(label)
    db.session.commit()

    assert label.id > 0
    assert product.id > 0
    assert len(label.meets_criteria) == 2
    assert len(label.resources) == 2
    assert label.products[0].name == 'Organic vegan gluten-free cookies'
    assert label.meets_criteria[0].satisfied is False
    assert label.meets_criteria[0].explanation == 'Nope.'
    assert label.meets_criteria[0].criterion.name == 'Saves the world'
    assert label.resources[0].name == 'cocoa'
    assert product.labels[0] == label
    assert resource_2.labels[0] == label


def test_origin_model(db):
    origin = m.Origin(name='Indonesia')

    db.session.add(origin)
    db.session.commit()

    assert origin.id > 0


def test_producer_model(db):
    producer = m.Producer(name='Willy Wonka’s Chocolate Factory')
    product = m.Product(name='Zucchini Chocolate', producer=producer)

    db.session.add(product)
    db.session.commit()

    assert producer.id > 0
    assert producer.products[0] == product
    assert product.producer == producer


def test_product_model(db):
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

    db.session.add(product)
    db.session.commit()

    assert product.id > 0
    assert organic.products[0] == product
    assert raw_palm_oil.ingredients[0].product == product
    assert raw_cocoa.ingredients[0].product == product  # Read: Raw cocoa used as an ingredient
    assert raw_cocoa.ingredients[0].origin == peru
    assert raw_cocoa.ingredients[0].supplier == supplier
    assert raw_cocoa.ingredients[0].percentage == 10
    assert peru.ingredients[0].product == product      # Read: Ingredients from Peru
    assert supplier.ingredients[0].product == product  # Read: Ingredients from this supplier
    assert billa.products[0] == product
    assert brand.products[0] == product
    assert producer.products[0] == product
    assert category.products[0] == product


def test_resource_model(db):
    resource = m.Resource(name='Cocoa')
    origin = m.Origin(name='Ghana')
    label = m.Label(name='Fairtrade')
    supplier = m.Supplier(name='XY')
    product = m.Product(name='Chocolate', labels=[label])
    ingredient = m.Ingredient(resource=resource, supplier=supplier, origin=origin, product=product)
    supply = m.Supply(resource=resource, supplier=supplier)

    resource.ingredients.append(ingredient)
    resource.supplies.append(supply)
    resource.labels.append(label)

    db.session.add(resource)
    db.session.commit()

    assert resource.id > 0
    assert resource.name == 'Cocoa'
    assert resource.labels[0] == label
    assert product.labels[0] in resource.labels
    assert resource.ingredients[0].origin == origin      # Read: Resource used as an ingredient
    assert resource.ingredients[0].supplier == supplier
    assert resource.supplies[0].supplier == supplier
    assert origin.ingredients[0].resource == resource    # Read: Ingredients from this origin
    assert product.ingredients[0].resource == resource
    assert supplier.ingredients[0].resource == resource  # Read: Ingredients from this supplier
    assert supplier.supplies[0].resource == resource     # Read: Supplies from this supplier


def test_retailer_model(db):
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

    db.session.add(retailer)
    db.session.commit()

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


def test_score_model(db):
    resource = m.Resource(name='pork fat')
    origin = m.Origin(name='austria')
    supplier = m.Supplier(name='huber-bauer')
    supply_from_country = m.Supply(resource=resource, origin=origin)
    supply_from_supplier = m.Supply(resource=resource, supplier=supplier)
    hotspot = m.Hotspot(name='animal rights')
    country_score = m.Score(
        supply=supply_from_country,
        hotspot=hotspot,
        score=3,
        explanation='foo'
    )
    supplier_score = m.Score(
        supply=supply_from_supplier,
        hotspot=hotspot,
        score=3,
        explanation='foo'
    )

    db.session.add(country_score, supplier_score)
    db.session.commit()

    assert country_score.supply.resource == resource
    assert country_score.supply.origin == origin
    assert country_score.supply.supplier is None
    assert country_score.hotspot == hotspot
    assert country_score.score == 3
    assert resource.supplies[1].scores[0] == country_score

    assert supplier_score.supply.resource == resource
    assert supplier_score.supply.origin is None
    assert supplier_score.supply.supplier == supplier
    assert resource.supplies[0].scores[0] == supplier_score


def test_store_model(db):
    retailer = m.Retailer(name='Rewe')
    store = m.Store(name='Billa', retailer=retailer)

    db.session.add(store)
    db.session.commit()

    assert store.id > 0
    assert store.retailer.id > 0
