import pytest
import json
import supermarket.api as api

url_for = api.api.url_for


@pytest.mark.usefixtures('client_class', 'db')
class TestProductApi:
    def test_post(self):
        res = self.client.post(
            url_for(api.ResourceList, type='products'),
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
            url_for(api.ResourceItem, type='products', id=2),
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
            url_for(api.ResourceItem, type='products', id=2),
            data=json.dumps({'name': 'Vanilla Ice Cream'}),
            content_type='application/json')
        assert res.status_code == 201
        assert res.mimetype == 'application/json'
        assert res.json['id'] == 2
        assert res.json['name'] == 'Vanilla Ice Cream'
        assert res.json['gtin'] is None

    def test_patch(self):
        res = self.client.patch(
            url_for(api.ResourceItem, type='products', id=2),
            data=json.dumps({'gtin': '11111111111111'}),
            content_type='application/json')
        assert res.status_code == 201
        assert res.mimetype == 'application/json'
        assert res.json['id'] == 2
        assert res.json['name'] == 'Vanilla Ice Cream'
        assert res.json['gtin'] == '11111111111111'

    def test_get(self):
        res = self.client.get(url_for(api.ResourceItem, type='products', id=1))
        assert res.status_code == 200
        assert res.mimetype == 'application/json'
        assert res.json['item']['id'] == 1
        assert res.json['item']['name'] == 'Organic cookies'
        assert res.json['item']['gtin'] == '99999999999999'
        assert res.json['item']['details']['currency'] == 'Euro'

    def test_get_all(self):
        res = self.client.get(url_for(api.ResourceList, type='products'))
        assert res.status_code == 200
        assert res.mimetype == 'application/json'
        assert res.json['items'][0]['id'] == 1
        assert res.json['items'][0]['name'] == 'Organic cookies'
        assert res.json['items'][0]['gtin'] == '99999999999999'
        assert res.json['items'][0]['details']['currency'] == 'Euro'
        assert res.json['items'][1]['id'] == 2
        assert res.json['items'][1]['name'] == 'Vanilla Ice Cream'
        assert res.json['items'][1]['gtin'] == '11111111111111'
        assert res.json['items'][1]['details'] is None

    def test_delete(self):
        res = self.client.delete(url_for(api.ResourceItem, type='products', id=2))
        assert res.status_code == 204

    def test_get_deleted(self):
        res = self.client.get(url_for(api.ResourceItem, type='products', id=2))
        assert res.status_code == 404

    def test_wrong_method(self):
        res = self.client.put(url_for(api.ResourceList, type='products'))
        assert res.status_code == 405


@pytest.mark.usefixtures('client_class', 'db')
class TestProductApiRelations:
    def test_post_new_relation(self):
        res = self.client.post(
            url_for(api.ResourceList, type='products'),
            data=json.dumps({
                'name': 'Organic cookies',
                'brand': {'name': 'Spar'}
            }),
            content_type='application/json')
        assert res.status_code == 201
        assert res.json['id'] == 1
        assert res.json['name'] == 'Organic cookies'
        assert res.json['brand'] == 1

        related_brand = self.client.get(
            url_for(api.ResourceItem, type='brands', id=res.json['brand']))
        assert related_brand.json['item']['name'] == 'Spar'
        assert related_brand.json['item']['products'][0] == 1

    def test_post_relation_as_id(self):
        res = self.client.post(
            url_for(api.ResourceList, type='products'),
            data=json.dumps({
                'name': 'Vanillia Ice Cream',
                'brand': 1
            }),
            content_type='application/json')
        assert res.status_code == 201
        assert res.json['id'] == 2
        assert res.json['brand'] == 1

        related_brand = self.client.get(
            url_for(api.ResourceItem, type='brands', id=res.json['brand']))
        assert 1 in related_brand.json['item']['products']
        assert 2 in related_brand.json['item']['products']

    def test_post_relation_with_id(self):
        res = self.client.post(
            url_for(api.ResourceList, type='products'),
            data=json.dumps({
                'name': 'Fluffy Cake',
                'brand': {'id': 1}
            }),
            content_type='application/json')
        assert res.status_code == 201
        assert res.json['id'] == 3
        assert res.json['brand'] == 1

        related_brand = self.client.get(
            url_for(api.ResourceItem, type='brands', id=res.json['brand']))
        assert 3 in related_brand.json['item']['products']


@pytest.mark.usefixtures('client_class', 'db')
class TestLabelApiRelations:
    def test_post_nested_relation(self):
        res = self.client.post(
            url_for(api.ResourceList, type='labels'),
            data=json.dumps({
                'name': {'en': 'A label'},
                'meets_criteria': [{
                    'criterion': {'name': 'A criterion'},
                    'score': '2'
                }]
            }),
            content_type='application/json')
        assert res.status_code == 201
        assert res.json['id'] == 1
        assert res.json['name'] == 'A label'
        assert res.json['meets_criteria'][0]['criterion'] == 1
        assert res.json['meets_criteria'][0]['score'] == 2

        related_criterion = self.client.get(
            url_for(api.ResourceItem, type='criteria',
                    id=res.json['meets_criteria'][0]['criterion']))
        assert related_criterion.json['item']['name'] == 'A criterion'


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
            url_for(api.ResourceList, type='products'),
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
            url_for(api.ResourceList, type='products'),
            data=json.dumps({
                'name': 'nonsense',
                'foo': 'bar',
                'gtin': 99999999999999
            }),
            content_type='application/json')
        self.assert_validation_failed(res)

    def test_put_nonsense(self):
        res = self.client.put(
            url_for(api.ResourceItem, type='products', id=1),
            data=json.dumps({
                'name': 'nonsense',
                'foo': 'bar',
                'gtin': 99999999999999
            }),
            content_type='application/json')
        self.assert_validation_failed(res)

    def test_patch_nonsense(self):
        res = self.client.patch(
            url_for(api.ResourceItem, type='products', id=1),
            data=json.dumps({'gtin': 99999999999999, 'foo': 'bar'}),
            content_type='application/json')
        self.assert_validation_failed(res)

    def test_post_bogus_relation(self):
        res = self.client.post(
            url_for(api.ResourceList, type='products'),
            data=json.dumps({
                'name': 'Organic cookies',
                'brand': 1
            }),
            content_type='application/json')
        assert res.status_code == 400
        assert res.mimetype == 'application/json'
        assert res.json['errors'][0]['field'] == 'brand'
        assert res.json['errors'][0]['messages'][0] == 'There is no brand with id 1.'


@pytest.mark.usefixtures('client_class', 'db')
class TestLabelApiTranslations:
    def test_post(self):
        res = self.client.post(
            url_for(api.ResourceList, type='labels'),
            data=json.dumps({"name": {"en": "A label", "de": "Ein Label"}}),
            content_type='application/json')
        print(res.json)
        assert res.status_code == 201
        assert res.mimetype == 'application/json'
        assert res.json['name'] == 'A label'

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=res.json['id'],
                                      lang='de'))
        assert res.json['item']['name'] == 'Ein Label'

    def test_get_item_with_lang(self):
        res = self.client.get(url_for(api.ResourceItem, type='labels', lang='en', id=1))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'A label'

        res = self.client.get(url_for(api.ResourceItem, type='labels', lang='de', id=1))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'Ein Label'

    def test_get_list_with_lang(self):
        res = self.client.get(url_for(api.ResourceList, type='labels', lang='en'))
        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'A label'

        res = self.client.get(url_for(api.ResourceList, type='labels', lang='de'))
        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Ein Label'

    def test_post_wrong_lang(self):
        res = self.client.post(
            url_for(api.ResourceList, type='labels'),
            data=json.dumps({
                'name': {'at': 'A label'}
            }),
            content_type='application/json')
        assert res.status_code == 400
        assert res.mimetype == 'application/json'
        assert res.json['errors'][0]['field'] == 'name'
        assert res.json['errors'][0]['messages'][0] == 'Invalid language (at).'

    def test_post_string(self):
        res = self.client.post(
            url_for(api.ResourceList, type='labels'),
            data=json.dumps({
                'name': 'A label'
            }),
            content_type='application/json')
        assert res.status_code == 400
        assert res.mimetype == 'application/json'
        assert res.json['errors'][0]['field'] == 'name'
        assert res.json['errors'][0]['messages'][0] == 'No language specified.'


@pytest.mark.usefixtures('client_class', 'db')
class TestLabelApiFilteringAndSorting:
    def test_post_labels(self):
        res = self.client.post(
            url_for(api.ResourceList, type='labels'),
            data=json.dumps({
                'type': 'product',
                'name': {'en': 'A'},
            }),
            content_type='application/json'
        )
        assert res.status_code == 201
        assert res.json['name'] == 'A'

        res = self.client.post(
            url_for(api.ResourceList, type='labels'),
            data=json.dumps({
                'type': 'product',
                'name': {'en': 'B'},
            }),
            content_type='application/json'
        )
        assert res.status_code == 201
        assert res.json['name'] == 'B'

    def test_reverse_sort_by_name_with_lang(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', lang='en', sort='-name')
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 2
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'
        assert res.json['items'][1]['name'] == 'A'

    def test_filter_by_name_with_lang(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', lang='en', name='B')
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_filter_greater_than_name_with_lang(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', lang='en', **{'name:gt': 'A'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_filter_greater_or_equal_name_with_lang(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', lang='en', **{'name:ge': 'B'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_filter_name_in_with_lang(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', lang='en', **{'name:in': 'B,C'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_filter_name_like_with_lang(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', lang='en', **{'name:like': 'B'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_filter_not_name_with_lang(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', lang='en', **{'name:ne': 'A'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_reverse_sort_by_name(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', sort='-name.en')
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 2
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'
        assert res.json['items'][1]['name'] == 'A'

    def test_filter_by_name(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', **{'name.en': 'B'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_filter_greater_than_name(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', **{'name.en:gt': 'A'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_filter_greater_or_equal_name(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', **{'name.en:ge': 'B'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_filter_name_in(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', **{'name.en:in': 'B,C'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_filter_name_like(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', **{'name.en:like': 'B'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_filter_not_name(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', **{'name.en:ne': 'A'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 1
        assert len(res.json['errors']) == 0
        assert res.json['items'][0]['name'] == 'B'

    def test_reverse_sort_unknown_field(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', sort='-nonsense')
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 2
        assert len(res.json['errors']) == 1
        assert res.json['errors'][0]['errors'][0]['value'] == '-nonsense'
        assert res.json['errors'][0]['errors'][0]['message'] == (
            'Unknown field `nonsense` for `labels`.')

    def test_filter_unknown_field(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', nonsense='A')
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 2
        assert len(res.json['errors']) == 1
        assert res.json['errors'][0]['errors'][0]['param'] == 'nonsense'
        assert res.json['errors'][0]['errors'][0]['message'] == (
            'Unknown field `nonsense` for `labels`.')

    def test_filter_unknown_operator(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', **{'name.en:xy': 'A'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 2
        assert len(res.json['errors']) == 1
        assert res.json['errors'][0]['errors'][0]['param'] == 'name.en:xy'
        assert res.json['errors'][0]['errors'][0]['message'].startswith('Unknown operator `xy`')

    def test_filter_like_integer(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', **{'id:like': '1'})
        )
        assert res.status_code == 200
        assert len(res.json['items']) == 2
        assert len(res.json['errors']) == 1
        assert res.json['errors'][0]['errors'][0]['param'] == 'id:like'
        assert res.json['errors'][0]['errors'][0]['message'] == 'Can’t compare integer to string.'


@pytest.mark.usefixtures('client_class', 'db')
class TestLabelApiPagination:
    def test_post_labels(self):
        res = self.client.post(
            url_for(api.ResourceList, type='labels'),
            data=json.dumps({
                'type': 'product',
                'name': {'en': 'A'},
            }),
            content_type='application/json'
        )
        assert res.status_code == 201
        assert res.json['name'] == 'A'

        res = self.client.post(
            url_for(api.ResourceList, type='labels'),
            data=json.dumps({
                'type': 'product',
                'name': {'en': 'B'},
            }),
            content_type='application/json'
        )
        assert res.status_code == 201
        assert res.json['name'] == 'B'

    def test_one_page(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels')
        )
        assert res.status_code == 200
        assert res.json['pages']['total'] == 1
        assert res.json['pages']['current'] == 1
        assert res.json['pages']['next_url'] is False
        assert res.json['pages']['prev_url'] is False

    def test_first_page_without_page_param(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', limit=1)
        )
        assert res.status_code == 200
        assert res.json['pages']['total'] == 2
        assert res.json['pages']['current'] == 1
        assert res.json['pages']['prev_url'] is False

        next_url = res.json['pages']['next_url']
        assert 'page=2' in next_url
        assert 'limit=1' in next_url
        assert self.client.get(next_url).status_code == 200

    def test_first_page_with_page_param(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', limit=1, page=1)
        )
        assert res.status_code == 200
        assert res.json['pages']['total'] == 2
        assert res.json['pages']['current'] == 1
        assert res.json['pages']['prev_url'] is False

        next_url = res.json['pages']['next_url']
        assert 'page=2' in next_url
        assert 'limit=1' in next_url
        assert self.client.get(next_url).status_code == 200

    def test_last_page(self):
        res = self.client.get(
            url_for(api.ResourceList, type='labels', limit=1, page=2)
        )
        assert res.status_code == 200
        assert res.json['pages']['total'] == 2
        assert res.json['pages']['current'] == 2
        assert res.json['pages']['next_url'] is False

        prev_url = res.json['pages']['prev_url']
        assert 'page=1' in prev_url
        assert 'limit=1' in prev_url
        assert self.client.get(prev_url).status_code == 200


@pytest.mark.usefixtures('client_class', 'db')
class TestApiDoc:
    def test_get_root_doc(self):
        res = self.client.get(url_for(api.RootDoc))
        assert res.status_code == 200
        assert res.mimetype == 'application/json'
        assert 'labels' in res.json
        assert 'products' in res.json
        assert self.client.get(res.json['labels']['list']).status_code == 200
        assert self.client.get(res.json['labels']['doc']).status_code == 200

    def test_get_label_doc(self):
        res = self.client.get(url_for(api.ResourceDoc, type='labels'))
        assert res.status_code == 200
        assert res.mimetype == 'application/json'
        assert len(res.json['fields']) == 13
