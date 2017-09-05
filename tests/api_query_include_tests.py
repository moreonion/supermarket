import pytest
import supermarket.api as api

url_for = api.api.url_for


@pytest.mark.usefixtures('client_class', 'db', 'example_data_brands')
class TestQueryInclude:
    def test_general(self):
        """ Check if we broke standard request. """
        url = url_for(api.ResourceItem, type='brands', id=1)
        res = self.client.get(url)

        assert res.status_code == 200
        assert res.json['name'] == 'Clever'

    def test_single_field(self):
        """ Check requesting a single field (products.name). """
        url = url_for(api.ResourceItem, type='brands', id=1, include='products.name')
        res = self.client.get(url)

        assert res.status_code == 200
        assert 'Chocolate chip cookies' in str(res.json['products'])

    def test_multi_fields(self):
        """ Check requesting multiple fields (products.id, products.name). """
        url = url_for(api.ResourceItem, type='brands', id=1, include='products.name,products.id')
        res = self.client.get(url)

        assert res.status_code == 200
        assert '\'id\': 1' in str(res.json['products'])
        assert 'Chocolate chip cookies' in str(res.json['products'])

    def test_all_fields(self):
        """ Check whether requesting all fields works (products.all) """
        url = url_for(api.ResourceItem, type='brands', id=1, include='products.all')
        res = self.client.get(url)

        assert res.status_code == 200
        assert '\'id\': 1' in str(res.json['products'])
        assert 'Chocolate chip cookies' in str(res.json['products'])

    def test_empty(self):
        """ Check whether the API can handle an empty include parameter. """
        url = url_for(api.ResourceItem, type='brands', id=1, include='')
        res = self.client.get(url)

        assert res.status_code == 200

    def test_whitespace(self):
        """ Check whether the API can handle whitespace seperated fields. """
        url = url_for(api.ResourceItem, type='brands', id=1, include='products.name, products.id')
        res = self.client.get(url)

        assert res.status_code == 200
