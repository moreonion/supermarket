import supermarket.model as m
from sqlalchemy.exc import IntegrityError
from pytest import raises


def test_label_model(db):
    t = m.Translation()
    name = m.TranslatedString(value='EU organic', language='en', field='name',
                              translation=t)
    description = m.TranslatedText(value='A cool label', language='en',
                                   field='description', translation=t)
    label = m.Label(
        translation=t,
        name=[name],
        description=[description],
        logo='some url',
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )

    t = m.Translation()
    exp = m.TranslatedText(value='Nope.', language='en', field='explanation',
                           translation=t)
    criterion_1_assoc = m.LabelMeetsCriterion(score=1, explanation=[exp], translation=t)
    t = m.Translation()
    name = m.TranslatedString(value='Saves the world', language='en', field='name',
                              translation=t)
    criterion_1_assoc.criterion = m.Criterion(name=[name], translation=t)
    label.meets_criteria.append(criterion_1_assoc)

    t = m.Translation()
    exp = m.TranslatedText(value='At least a few of us…', language='en',
                           field='explanation', translation=t)
    criterion_2_assoc = m.LabelMeetsCriterion(score=2, explanation=[exp], translation=t)
    t = m.Translation()
    name = m.TranslatedString(value='Makes us all happy', language='en', field='name',
                              translation=t)
    criterion_2_assoc.criterion = m.Criterion(name=[name], translation=t)
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
    assert label.meets_criteria[0].score is 1
    assert label.meets_criteria[0].explanation[0].value == 'Nope.'
    assert label.meets_criteria[0].criterion.name[0].value == 'Saves the world'
    assert label.resources[0].name == 'cocoa'
    assert label.countries[0].code == 'AT'
    assert product.labels[0] == label
    assert resource_2.labels[0] == label


def test_label_model_empty_name(db):
    t = m.Translation()
    name = m.TranslatedString(value='', language='en', field='name',
                              translation=t)
    description = m.TranslatedText(value='A cool label.', language='en',
                                   field='description', translation=t)
    label = m.Label(
        name=[name],
        description=[description],
        logo='some url',
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )

    db.session.add(label)

    with raises(IntegrityError):
        db.session.commit()


def test_label_model_duplicate_name(db):
    t = m.Translation()
    name = m.TranslatedString(value='A unique name', language='en', translation=t,
                              field='name')
    description = m.TranslatedText(value='A cool label.', language='en',
                                   translation=t, field='description')
    label = m.Label(
        name=[name],
        description=[description],
        logo='some url',
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )
    t = m.Translation()
    name = m.TranslatedString(value='A unique name', language='en', translation=t,
                              field='name')
    description = m.TranslatedText(value='A cool label.', language='en',
                                   translation=t, field='description')
    label2 = m.Label(
        name=[name],
        description=[description],
        logo='some url',
        countries=[m.LabelCountry(code='GB'), m.LabelCountry(code='AT')]
    )

    db.session.add(label)
    db.session.add(label2)

    with raises(IntegrityError):
        db.session.commit()
