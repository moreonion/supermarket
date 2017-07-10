import pytest
import json
import supermarket.api as api

url_for = api.api.url_for


@pytest.mark.usefixtures('client_class', 'db')
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

    def test_put_new(self):
        res = self.client.put(
            url_for(api.Product, id=2),
            data=json.dumps({
                'name': 'Chocolate Ice Cream',
                'gtin': '11111111111111'
            }),
            content_type='application/json')
        assert res.status_code == 201
        assert res.mimetype == 'application/json'
        assert res.json['id'] == 2
        assert res.json['name'] == 'Chocolate Ice Cream'
        assert res.json['gtin'] == '11111111111111'
        assert res.json['details'] is None

    def test_put_existing(self):
        res = self.client.put(
            url_for(api.Product, id=2),
            data=json.dumps({'name': 'Vanilla Ice Cream'}),
            content_type='application/json')
        assert res.status_code == 201
        assert res.mimetype == 'application/json'
        assert res.json['id'] == 2
        assert res.json['name'] == 'Vanilla Ice Cream'
        assert res.json['gtin'] is None

    def test_patch(self):
        res = self.client.patch(
            url_for(api.Product, id=2),
            data=json.dumps({'gtin': '11111111111111'}),
            content_type='application/json')
        assert res.status_code == 201
        assert res.mimetype == 'application/json'
        assert res.json['id'] == 2
        assert res.json['name'] == 'Vanilla Ice Cream'
        assert res.json['gtin'] == '11111111111111'

    def test_get(self):
        res = self.client.get(url_for(api.Product, id=1))
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
        assert res.json[1]['id'] == 2
        assert res.json[1]['name'] == 'Vanilla Ice Cream'
        assert res.json[1]['gtin'] == '11111111111111'
        assert res.json[1]['details'] is None

    def test_delete(self):
        res = self.client.delete(url_for(api.Product, id=2))
        assert res.status_code == 204

    def test_get_deleted(self):
        res = self.client.get(url_for(api.Product, id=2))
        assert res.status_code == 404

    def test_wrong_method(self):
        res = self.client.put(url_for(api.ProductList))
        assert res.status_code == 405


@pytest.mark.usefixtures('client_class', 'db')
class TestProductApiValidation:
    @classmethod
    def assert_validation_failed(cls, res):
        assert res.status_code == 400
        assert res.mimetype == 'application/json'
        assert len(res.json['errors']) == 2
        for error in res.json['errors']:
            if error['field'] == 'gtin':
                assert error['messages'][0] == 'Not a valid string.'
            if error['field'] == 'foo':
                assert error['messages'][0] == 'Unknown field.'

    def test_post_valid(self):
        res = self.client.post(
            url_for(api.ProductList),
            data=json.dumps({
                'name': 'Organic cookies',
                'gtin': '99999999999999'
            }),
            content_type='application/json')
        assert res.status_code == 201
        assert res.mimetype == 'application/json'
        assert res.json['id'] == 1
        assert res.json['name'] == 'Organic cookies'
        assert res.json['gtin'] == '99999999999999'

    def test_post_nonsense(self):
        res = self.client.post(
            url_for(api.ProductList),
            data=json.dumps({
                'name': 'nonsense',
                'foo': 'bar',
                'gtin': 99999999999999
            }),
            content_type='application/json')
        self.assert_validation_failed(res)

    def test_put_nonsense(self):
        res = self.client.put(
            url_for(api.Product, id=1),
            data=json.dumps({
                'name': 'nonsense',
                'foo': 'bar',
                'gtin': 99999999999999
            }),
            content_type='application/json')
        self.assert_validation_failed(res)

    def test_patch_nonsense(self):
        res = self.client.patch(
            url_for(api.Product, id=1),
            data=json.dumps({'gtin': 99999999999999, 'foo': 'bar'}),
            content_type='application/json')
        self.assert_validation_failed(res)
