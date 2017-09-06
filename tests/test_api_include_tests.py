import pytest
import supermarket.api as api

url_for = api.api.url_for


@pytest.mark.usefixtures('client_class', 'db', 'example_data_brands')
class TestQueryInclude:

    """ Tests for the ?include=field1,field2,... GET parameter. """

    def test_general(self):
        """ Check if we broke requests without any parameters. """
        url = url_for(api.ResourceItem, type='brands', id=1)
        res = self.client.get(url)

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Clever'

        url = url_for(api.ResourceList, type='brands')
        res = self.client.get(url)

        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Clever'

    def test_single_field(self):
        """ Check requesting a single field (products.name). """
        url = url_for(api.ResourceItem, type='brands', id=1, include='products.name')
        res = self.client.get(url)

        assert res.status_code == 200
        assert 'Chocolate chip cookies' in str(res.json['item']['products'])

        url = url_for(api.ResourceList, type='brands', include='products.name')
        res = self.client.get(url)

        assert res.status_code == 200
        assert 'Chocolate chip cookies' in str(res.json['items'][0]['products'])

    def test_multi_fields(self):
        """ Check requesting multiple fields (products.id, products.name). """
        url = url_for(api.ResourceItem, type='brands', id=1, include='products.name,products.id')
        res = self.client.get(url)

        assert res.status_code == 200
        assert '\'id\': 1' in str(res.json['item']['products'])
        assert 'Chocolate chip cookies' in str(res.json['item']['products'])

        url = url_for(api.ResourceList, type='brands', include='products.name,products.id')
        res = self.client.get(url)

        assert res.status_code == 200
        assert '\'id\': 1' in str(res.json['items'][0]['products'])
        assert 'Chocolate chip cookies' in str(res.json['items'][0]['products'])

    def test_all_fields(self):
        """ Check whether requesting all fields works (products.all) """
        url = url_for(api.ResourceItem, type='brands', id=1, include='products.all')
        res = self.client.get(url)

        assert res.status_code == 200
        assert '\'id\': 1' in str(res.json['item']['products'])
        assert 'Chocolate chip cookies' in str(res.json['item']['products'])

        url = url_for(api.ResourceList, type='brands', include='products.all')
        res = self.client.get(url)

        assert res.status_code == 200
        assert '\'id\': 1' in str(res.json['items'][0]['products'])
        assert 'Chocolate chip cookies' in str(res.json['items'][0]['products'])

    def test_empty(self):
        """ Check whether the API can handle an empty include parameter. """
        url = url_for(api.ResourceItem, type='brands', id=1, include='')
        res = self.client.get(url)

        assert res.status_code == 200

        url = url_for(api.ResourceList, type='brands', include='')
        res = self.client.get(url)

        assert res.status_code == 200

    def test_whitespace(self):
        """ Check whether the API can handle whitespace seperated fields. """
        url = url_for(api.ResourceItem, type='brands', id=1, include='products.adsf, products.id')
        res = self.client.get(url)

        assert res.status_code == 200
        assert '\'id\': 1' in str(res.json['item']['products'])
        assert 'Chocolate chip cookies' not in str(res.json['item']['products'])

        url = url_for(api.ResourceList, type='brands', include='products.adsf, products.id')
        res = self.client.get(url)

        assert res.status_code == 200
        assert '\'id\': 1' in str(res.json['items'][0]['products'])
        assert 'Chocolate chip cookies' not in str(res.json['items'][0]['products'])

    def test_invalid_args(self):
        """ Check whether invalid field names trigger error messages. """
        url = url_for(api.ResourceItem, type='brands', id=1, include='products.adsf, products.id')
        res = self.client.get(url)

        assert res.status_code == 200
        assert 'Unknown field `adsf`' in str(res.json['errors'])
        assert '\'id\': 1' in str(res.json['item']['products'])
        assert 'Chocolate chip cookies' not in str(res.json['item']['products'])

        url = url_for(api.ResourceList, type='brands', include='products.adsf, products.id')
        res = self.client.get(url)

        assert res.status_code == 200
        assert 'Unknown field `adsf`' in str(res.json['errors'])
        assert '\'id\': 1' in str(res.json['items'][0]['products'])
        assert 'Chocolate chip cookies' not in str(res.json['items'][0]['products'])
