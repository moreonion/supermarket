import pytest


import json
import supermarket.api as api


url_for = api.api.url_for


@pytest.mark.usefixtures('client_class', 'session_class')
class TestProductApi:
    def test_post(self):
        res = self.client.post(
            url_for(api.ProductList),
            data=json.dumps({
                'name': 'Organic cookies',
                'gtin': '99999999999999',
                'details': {
                    'price': '2,99',
                    'currency': 'Euro'
                }
            }),
            content_type='application/json')
        assert res.status_code == 201
        assert res.mimetype == 'application/json'
        assert res.json['id'] == 1
        assert res.json['name'] == 'Organic cookies'
        assert res.json['gtin'] == '99999999999999'
        assert res.json['details']['currency'] == 'Euro'

    def test_get(self):
        res = self.client.get(url_for(api.Product, product_id=1))
        assert res.status_code == 200
        assert res.mimetype == 'application/json'
        assert res.json['id'] == 1
        assert res.json['name'] == 'Organic cookies'
        assert res.json['gtin'] == '99999999999999'
        assert res.json['details']['currency'] == 'Euro'

    def test_get_all(self):
        res = self.client.get(url_for(api.ProductList))
        assert res.status_code == 200
        assert res.mimetype == 'application/json'
        assert res.json[0]['id'] == 1
        assert res.json[0]['name'] == 'Organic cookies'
        assert res.json[0]['gtin'] == '99999999999999'
        assert res.json[0]['details']['currency'] == 'Euro'

    def test_put(self):
        res = self.client.put(
            url_for(api.Product, product_id=1),
            data=json.dumps({'name': 'Vegan cookies'}),
            content_type='application/json')
        assert res.status_code == 201
        assert res.json['id'] == 1
        assert res.json['name'] == 'Vegan cookies'
        assert res.json['gtin'] == '99999999999999'
        assert res.json['details']['currency'] == 'Euro'
        assert res.mimetype == 'application/json'

    def test_delete(self):
        res = self.client.delete(url_for(api.Product, product_id=1))
        assert res.status_code == 204

    def test_get_deleted(self):
        res = self.client.get(url_for(api.Product, product_id=1))
        assert res.status_code == 404
