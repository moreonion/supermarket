from supermarket.model import *


def test_retailer_model(session):
    retailer = Retailer(name='Rewe')
    Store(name='Billa', retailer=retailer)
    Store(name='Penny', retailer=retailer)
    Brand(name='Clever', retailer=retailer)

    session.add(retailer)
    session.commit()

    assert retailer.id > 0
    assert len(retailer.stores) == 2
    assert len(retailer.brands) == 1


def test_store_model(session):
    retailer = Retailer(name='Rewe')
    store = Store(name='Billa', retailer=retailer)

    session.add(store)
    session.commit()

    assert store.id > 0
    assert store.retailer.id > 0
