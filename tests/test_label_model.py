import supermarket.model as m
from sqlalchemy.exc import IntegrityError
from pytest import raises


def test_label_model(db):
    label = m.Label(
        name={'en': 'EU organic', 'de': 'EU Bio'},
        description={'en': 'A cool label.', 'de': 'Ein cooles Label'},
        logo={'en': 'some url'},
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )

    measure_1_assoc = m.Measure(score=1, explanation={'en': 'Nope.'})
    measure_1_assoc.criterion = m.Criterion(name={'en': 'Saves the world'})
    label.meets_criteria.append(measure_1_assoc)

    measure_2_assoc = m.Measure(score=2, explanation={'en': 'At least a few of us…'})
    measure_2_assoc.criterion = m.Criterion(name={'en': 'Makes us all happy'})
    label.meets_criteria.append(measure_2_assoc)

    resource_1 = m.Resource(name={'en': 'cocoa'})
    resource_2 = m.Resource(name={'en': 'palm oil'})
    label.resources = [resource_1, resource_2]

    product = m.Product(name={'en': 'Organic vegan gluten-free cookies'})
    label.products.append(product)

    db.session.add(label)
    db.session.commit()

    assert label.id > 0
    assert product.id > 0
    assert len(label.meets_criteria) == 2
    assert len(label.resources) == 2
    assert label.name['en'] == 'EU organic'
    assert label.name['de'] == 'EU Bio'
    assert label.products[0].name['en'] == 'Organic vegan gluten-free cookies'
    assert label.meets_criteria[0].score is 1
    assert label.meets_criteria[0].explanation['en'] == 'Nope.'
    assert label.meets_criteria[0].criterion.name['en'] == 'Saves the world'
    assert label.resources[0].name['en'] == 'cocoa'
    assert label.countries[0].code == 'AT'
    assert product.labels[0] == label
    assert resource_2.labels[0] == label


def test_label_model_no_name(db):
    label = m.Label(
        description={'en': 'A cool label.'},
        logo={'en': 'some url'},
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )

    db.session.add(label)

    with raises(IntegrityError):
        db.session.commit()


def test_label_model_duplicate_name(db):
    label = m.Label(
        name={'en': 'A unique name'},
        description={'en': 'A cool label.'},
        logo={'en': 'some url'},
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )
    label2 = m.Label(
        name={'en': 'A unique name'},
        description={'en': 'A cool label.'},
        logo={'en': 'some url'},
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )

    db.session.add(label)
    db.session.add(label2)

    with raises(IntegrityError):
        db.session.commit()


def test_label_model_meets_duplicate_criteria(db):
    label = m.Label(name={'en': 'A cool label'})
    criterion = m.Criterion(name={'en': 'Saves the world'})

    label.meets_criteria.append(m.Measure(score=1, criterion=criterion))
    label.meets_criteria.append(m.Measure(score=2, criterion=criterion))
    db.session.add(label)

    with raises(IntegrityError):
        db.session.commit()
