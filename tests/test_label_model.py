import supermarket.model as m
from sqlalchemy.exc import IntegrityError
from pytest import raises


def test_label_model(db):
    label = m.Label(
        name={'en': 'EU organic', 'de': 'EU Bio'},
        description={'en': 'A cool label.', 'de': 'Ein cooles Label'},
        logo='some url',
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )

    criterion_1_assoc = m.LabelMeetsCriterion(score=1, explanation='Nope.')
    criterion_1_assoc.criterion = m.Criterion(name='Saves the world')
    label.meets_criteria.append(criterion_1_assoc)

    criterion_2_assoc = m.LabelMeetsCriterion(score=2, explanation='At least a few of us…')
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
    assert label.name['en'] == 'EU organic'
    assert label.name['de'] == 'EU Bio'
    assert label.products[0].name == 'Organic vegan gluten-free cookies'
    assert label.meets_criteria[0].score is 1
    assert label.meets_criteria[0].explanation == 'Nope.'
    assert label.meets_criteria[0].criterion.name == 'Saves the world'
    assert label.resources[0].name == 'cocoa'
    assert label.countries[0].code == 'AT'
    assert product.labels[0] == label
    assert resource_2.labels[0] == label


def test_label_model_no_name(db):
    label = m.Label(
        description='A cool label.',
        logo='some url',
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )

    db.session.add(label)

    with raises(IntegrityError):
        db.session.commit()


def test_label_model_duplicate_name(db):
    label = m.Label(
        name={'en': 'A unique name'},
        description={'en': 'A cool label.'},
        logo='some url',
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )
    label2 = m.Label(
        name={'en': 'A unique name'},
        description={'en': 'A cool label.'},
        logo='some url',
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )

    db.session.add(label)
    db.session.add(label2)

    with raises(IntegrityError):
        db.session.commit()
