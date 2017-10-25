import json
import pytest
import supermarket.api as api

url_for = api.api.url_for


class Util:
    # Label #1: English & German
    lbl1_name = 'English and German'
    lbl1_name_de = 'Englisch und Deutsch'
    lbl1_description = 'English description'
    lbl1_description_de = 'Deutsche Beschreibung'
    # Label #2: English only
    lbl2_name = 'English only'
    lbl2_description = 'English description only'
    # Label #3: German only
    lbl3_name = 'Nur Deutsch'
    lbl3_description = 'Nur eine deutsche Beschreibung'
    # Criterion #1: Label #1
    crit1_explanation = 'The label is both English and German.'
    crit1_explanation_de = 'Das Label ist sowohl Deutsch, als auch Englisch.'
    # Criterion #2: Label #2
    crit2_explanation = 'The label is at least in English, so a lot of people will understand it.'
    # Criterion #3: Label #3
    crit3_explanation = 'Alles nur Deutsch.'

    # A label for POST testing
    lbl4_name = 'A posted label'
    lbl4_name_de = 'Ein gepostetes Label'
    lbl4_description = 'This label was posted to the ResourceList!'
    lbl4_description_de = 'Dieses Label wurde auf die ResourceList gepostet!'
    lbl4_logo = 'posted_logo.png'
    lbl4_logo_de = 'posted_german_logo.png'

    # A label for PUT testing
    lbl5_name = 'A putted label'
    lbl5_name_de = 'Ein geputtetes Label'
    lbl5_description = 'This label was put on another one!'
    lbl5_description_de = 'Dieses Label wurde auf ein anderes geputtet!'

    # A label for PATCH testing
    lbl6_name = 'A patched label'
    lbl6_name_de = 'Ein gepachtes Label'
    lbl6_description = 'This label has been patched!'
    lbl6_description_de = 'Dieses Label wurde gepatcht!'


@pytest.mark.usefixtures('client_class', 'db', 'example_data_label_guide')
class TestLabels:
    """Tests all HTTP verbs of the Label schema. GET is already implemented
    in TestLabelGuideUseCases"""
    def test_post_to_list(self):
        res = self.client.post(url_for(api.ResourceList, type='labels'),
                               data=json.dumps(
                                   {"name": {"en": Util.lbl4_name,
                                             "de": Util.lbl4_name_de},
                                    "description": {
                                        "en": Util.lbl4_description,
                                        "de": Util.lbl4_description_de},
                                    "logo": {
                                        "en": Util.lbl4_logo,
                                        "de": Util.lbl4_logo_de},
                                    "meets_criteria": [{"criterion": 1}],
                                    }),
                               content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == Util.lbl4_name
        assert res.json['name']['de'] == Util.lbl4_name_de
        assert res.json['description']['en'] == Util.lbl4_description
        assert res.json['description']['de'] == Util.lbl4_description_de
        assert res.json['logo']['en'] == Util.lbl4_logo
        assert res.json['logo']['de'] == Util.lbl4_logo_de
        id = res.json['id']

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=id))

        assert res.status_code == 200
        assert res.json['item']['name']['en'] == Util.lbl4_name
        assert res.json['item']['name']['de'] == Util.lbl4_name_de
        assert res.json['item']['description']['en'] == Util.lbl4_description
        assert res.json['item']['description']['de'] == Util.lbl4_description_de
        assert res.json['item']['logo']['en'] == Util.lbl4_logo
        assert res.json['item']['logo']['de'] == Util.lbl4_logo_de

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=id, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == Util.lbl4_name_de
        assert res.json['item']['description'] == Util.lbl4_description_de
        assert res.json['item']['logo'] == Util.lbl4_logo_de

        # What's our return value if we don't post an English value?
        res = self.client.post(url_for(api.ResourceList, type='labels'),
                               data=json.dumps(
                                   {"name": {"de": Util.lbl4_name_de},
                                    "description": {"de": Util.lbl4_description_de},
                                    "logo": {"de": Util.lbl4_logo_de},
                                    "meets_criteria": [{"criterion": 3}],
                                    }),
                               content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['de'] == Util.lbl4_name_de
        assert res.json['description']['de'] == Util.lbl4_description_de
        assert res.json['logo']['de'] == Util.lbl4_logo_de

    def test_put_item(self):
        # Replace first label's data with new data
        res = self.client.put(url_for(api.ResourceItem, type='labels', id=1),
                              data=json.dumps(
                                  {"name": {"de": Util.lbl5_name_de},
                                   "description": {
                                       "en": Util.lbl5_description,
                                       "de": Util.lbl5_description_de},
                                   "meets_criteria": [{"criterion": 1}],
                                   }),
                              content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['de'] == Util.lbl5_name_de
        assert res.json['description']['en'] == Util.lbl5_description
        assert res.json['description']['de'] == Util.lbl5_description_de
        assert res.json['meets_criteria'][0]['criterion'] == 1

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=1))

        assert res.status_code == 200
        assert res.json['item']['name']['de'] == Util.lbl5_name_de
        assert res.json['item']['description']['en'] == Util.lbl5_description
        assert res.json['item']['description']['de'] == Util.lbl5_description_de
        assert res.json['item']['meets_criteria'][0]['criterion'] == 1

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=1, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == Util.lbl5_name_de
        assert res.json['item']['description'] == Util.lbl5_description_de
        assert res.json['item']['meets_criteria'][0]['criterion'] == 1

    def test_patch_item(self):
        # Update the German only label's data by adding English values
        res = self.client.patch(url_for(api.ResourceItem, type='labels', id=3),
                                data=json.dumps(
                                    {"name": {"en": Util.lbl6_name},
                                     "description": {"en": Util.lbl6_description},
                                     "meets_criteria": [{"criterion": 1}]}),
                                content_type='application/json'
                                )

        assert res.status_code == 201
        assert res.json['name']['en'] == Util.lbl6_name
        assert res.json['description']['en'] == Util.lbl6_description
        assert res.json['meets_criteria'][0]['criterion'] == 1

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=3))

        assert res.status_code == 200
        assert res.json['item']['name']['en'] == Util.lbl6_name
        assert res.json['item']['description']['en'] == Util.lbl6_description
        assert res.json['item']['meets_criteria'][0]['criterion'] == 1

    def test_delete_item(self):
        # Delete a whole item
        res = self.client.delete(url_for(api.ResourceItem, type='labels', id=1))
        assert res.status_code == 204

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=1))
        assert res.status_code == 404


@pytest.mark.usefixtures('client_class', 'db', 'example_data_resources')
class TestResources:
    def test_get_from_list(self):
        res = self.client.get(url_for(api.ResourceList, type='resources'))
        assert res.status_code == 200
        assert res.json['items'][0]['name']['en'] == 'English Test Resource'
        assert res.json['items'][1]['name']['de'] == 'Deutsche Test Resource'
        assert res.json['items'][2]['name']['en'] == 'Multilingual Test Resource'
        assert res.json['items'][2]['name']['de'] == 'Mehrsprachige Test Resource'

        res = self.client.get(url_for(api.ResourceList, type='resources', lang='de'))
        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'English Test Resource'
        assert res.json['items'][1]['name'] == 'Deutsche Test Resource'
        assert res.json['items'][2]['name'] == 'Mehrsprachige Test Resource'

    def test_get_item(self):
        res = self.client.get(url_for(api.ResourceItem, type='resources', id=3))
        assert res.status_code == 200
        assert res.json['item']['name']['en'] == 'Multilingual Test Resource'
        assert res.json['item']['name']['de'] == 'Mehrsprachige Test Resource'

        res = self.client.get(url_for(api.ResourceItem, type='resources', id=3, lang='de'))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'Mehrsprachige Test Resource'

    def test_post_to_list(self):
        res = self.client.post(
            url_for(api.ResourceList, type='resources'),
            data=json.dumps({'name': {'en': 'Herbal Tea', 'de': 'Herber Tee'}}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'Herbal Tea'
        assert res.json['name']['de'] == 'Herber Tee'

        res = self.client.get(url_for(api.ResourceItem, type='resources',
                                      id=res.json['id'], lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Herber Tee'

    def test_put_item(self):
        res = self.client.put(
            url_for(api.ResourceItem, type='resources', id=1),
            data=json.dumps({
                'name': {'en': 'I put that here',
                         'de': 'Ich leg\'s hier hin'}}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'I put that here'
        assert res.json['name']['de'] == 'Ich leg\'s hier hin'

        res = self.client.get(url_for(api.ResourceItem, type='resources',
                                      id=1, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Ich leg\'s hier hin'

    def test_patch_item(self):
        res = self.client.patch(
            url_for(api.ResourceItem, type='resources', id=2),
            data=json.dumps({'name': {'en': 'That should fix it...',
                                      'de': 'Sollte wieder gehn.'}}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'That should fix it...'
        assert res.json['name']['de'] == 'Sollte wieder gehn.'

        res = self.client.get(url_for(api.ResourceItem, type='resources',
                                      id=2, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Sollte wieder gehn.'

    def test_delete_item(self):
        res = self.client.delete(url_for(api.ResourceItem, type='resources', id=3))
        assert res.status_code == 204

        res = self.client.get(url_for(api.ResourceItem, type='resources', id=3))
        assert res.status_code == 404


@pytest.mark.usefixtures('client_class', 'db', 'example_data_hotspots')
class TestHotspots:
    def test_get_from_list(self):
        res = self.client.get(url_for(api.ResourceList, type='hotspots'))

        assert res.status_code == 200
        assert res.json['items'][0]['name']['en'] == 'Multilingual hotspot'
        assert res.json['items'][0]['name']['de'] == 'Mehrsprachiger hotspot'
        assert res.json['items'][0]['description']['en'] == (
            'This hotspot speaks 2 languages')
        assert res.json['items'][0]['description']['de'] == (
            'Dieser hotspot spricht 2 sprachen')
        assert res.json['items'][1]['name']['en'] == 'English hotspot'
        assert res.json['items'][1]['description']['en'] == (
            'This hotspot speaks English')
        assert res.json['items'][2]['name']['de'] == 'Deutscher hotspot'
        assert res.json['items'][2]['description']['de'] == (
            'Dieser hotspot spricht deutsch')

        res = self.client.get(url_for(api.ResourceList, type='hotspots', lang='de'))

        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Mehrsprachiger hotspot'
        assert res.json['items'][0]['description'] == (
            'Dieser hotspot spricht 2 sprachen')
        assert res.json['items'][1]['name'] == 'English hotspot'
        assert res.json['items'][1]['description'] == (
            'This hotspot speaks English')
        assert res.json['items'][2]['name'] == 'Deutscher hotspot'
        assert res.json['items'][2]['description'] == (
            'Dieser hotspot spricht deutsch')

    def test_get_single_item(self):
        res = self.client.get(url_for(api.ResourceItem, type='hotspots', id=1))

        assert res.status_code == 200
        assert res.json['item']['name']['en'] == 'Multilingual hotspot'
        assert res.json['item']['name']['de'] == 'Mehrsprachiger hotspot'
        assert res.json['item']['description']['en'] == (
            'This hotspot speaks 2 languages')
        assert res.json['item']['description']['de'] == (
            'Dieser hotspot spricht 2 sprachen')

        res = self.client.get(url_for(api.ResourceItem, type='hotspots', id=1, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Mehrsprachiger hotspot'
        assert res.json['item']['description'] == (
            'Dieser hotspot spricht 2 sprachen')

    def test_post_to_list(self):
        res = self.client.post(
            url_for(api.ResourceList, type='hotspots'),
            data=json.dumps({'name': {'en': 'New hotspot',
                                      'de': 'Neuer hotspot'},
                             'description': {
                                 'en': 'A brandnew hotspot!',
                                 'de': 'Ein brennender hotspot!'}}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'New hotspot'
        assert res.json['description']['en'] == 'A brandnew hotspot!'

        res = self.client.get(url_for(api.ResourceItem, type='hotspots',
                                      id=res.json['id'], lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Neuer hotspot'
        assert res.json['item']['description'] == 'Ein brennender hotspot!'

    def test_put_item(self):
        res = self.client.put(
            url_for(api.ResourceItem, type='hotspots', id=2),
            data=json.dumps({'name': {'en': 'Slowly multilingual',
                                      'de': 'Langsam mehrsprachig'},
                             'description': {'en': 'Good things take time',
                                             'de': 'Gut Ding braucht Weile'}}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'Slowly multilingual'
        assert res.json['name']['de'] == 'Langsam mehrsprachig'
        assert res.json['description']['en'] == 'Good things take time'
        assert res.json['description']['de'] == 'Gut Ding braucht Weile'

        res = self.client.get(url_for(api.ResourceItem, type='hotspots',
                                      id=2, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Langsam mehrsprachig'
        assert res.json['item']['description'] == 'Gut Ding braucht Weile'

    def test_patch_item(self):
        res = self.client.patch(
            url_for(api.ResourceItem, type='hotspots', id=3),
            data=json.dumps({'name': {'de': 'Immer noch deutsch :('},
                             'description': {'de': 'Ohje'}}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['de'] == 'Immer noch deutsch :('
        assert res.json['description']['de'] == 'Ohje'

        res = self.client.get(url_for(api.ResourceItem, type='hotspots', id=3))

        assert res.status_code == 200
        assert res.json['item']['name']['de'] == 'Immer noch deutsch :('
        assert res.json['item']['description']['de'] == 'Ohje'

    def test_delete_item(self):
        res = self.client.delete(url_for(api.ResourceItem, type='hotspots', id=3))
        assert res.status_code == 204

        res = self.client.get(url_for(api.ResourceItem, type='hotspots', id=3))
        assert res.status_code == 404


@pytest.mark.usefixtures('client_class', 'db', 'example_data_scores')
class TestSupplies:
    def test_get_from_list(self):
        # Test default
        res = self.client.get(url_for(api.ResourceList, type='supplies'))

        assert res.status_code == 200
        assert res.json['items'][0]['scores'][0]['explanation']['de'] == (
            'Diese Erklaerung ist auf deutsch.')
        assert res.json['items'][1]['scores'][0]['explanation']['en'] == (
            'This explanation is in English.')
        assert res.json['items'][2]['scores'][0]['explanation']['en'] == (
            'This explanation is multilingual!')
        assert res.json['items'][2]['scores'][0]['explanation']['de'] == (
            'Diese Erklaerung ist mehrsprachig!')

        res = self.client.get(url_for(api.ResourceList, type='supplies', lang='de'))

        assert res.status_code == 200
        assert res.json['items'][0]['scores'][0]['explanation'] == (
            'Diese Erklaerung ist auf deutsch.')
        assert res.json['items'][1]['scores'][0]['explanation'] == (
            'This explanation is in English.')
        assert res.json['items'][2]['scores'][0]['explanation'] == (
            'Diese Erklaerung ist mehrsprachig!')

    def test_get_item(self):
        res = self.client.get(url_for(api.ResourceItem, type='supplies', id=3))

        assert res.status_code == 200
        assert res.json['item']['scores'][0]['explanation']['en'] == (
            'This explanation is multilingual!')
        assert res.json['item']['scores'][0]['explanation']['de'] == (
            'Diese Erklaerung ist mehrsprachig!')

        res = self.client.get(url_for(api.ResourceItem, type='supplies', id=3, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['scores'][0]['explanation'] == 'Diese Erklaerung ist mehrsprachig!'

    def test_post_to_list(self):
        res = self.client.post(
            url_for(api.ResourceList, type='supplies'),
            data=json.dumps({'resource': {'name': {'en': 'POST resource'}},
                             'scores': [{
                                 'hotspot': {'name': {'en': 'POST hotspot'}},
                                 'explanation': {'en': 'I just posted this here.',
                                                 'de': 'Wurde gePOSTet.'},
                                 'score': 99
                             }]}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['scores'][0]['explanation']['en'] == 'I just posted this here.'

        res = self.client.get(url_for(api.ResourceItem, type='supplies', id=res.json['id'],
                                      lang='de'))

        assert res.status_code == 200
        assert res.json['item']['scores'][0]['explanation'] == 'Wurde gePOSTet.'

    def test_put_item(self):
        res = self.client.put(
            url_for(api.ResourceItem, type='supplies', id=1),
            data=json.dumps({'resource': {'name': {'en': 'PUT'}},
                             'supplier': {'name': 'PUT-Dealer'},
                             'scores': [{
                                 'hotspot': {'name': {'en': 'All PUT, no GET'}},
                                 'explanation': {'en': 'I just put that here for a minute.',
                                                 'de': 'Ich stell das kurz hier hin.'},
                                 'score': 999
                                 }]}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['scores'][0]['explanation']['en'] == 'I just put that here for a minute.'

        res = self.client.get(url_for(api.ResourceItem, type='supplies', id=1, lang='de'))
        assert res.status_code == 200
        assert res.json['item']['scores'][0]['explanation'] == 'Ich stell das kurz hier hin.'

    def test_patch_item(self):
        res = self.client.patch(
            url_for(api.ResourceItem, type='supplies', id=1),
            data=json.dumps({
                'scores': [{
                    'hotspot': {'name': {'en': 'All PUT, no GET'}},
                    'explanation': {'en': 'Ok, patch will take care of it.'},
                    'score': 100}]}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['scores'][0]['explanation']['en'] == 'Ok, patch will take care of it.'

    def test_delete_item(self):
        res = self.client.delete(url_for(api.ResourceItem, type='supplies', id=1))
        assert res.status_code == 204

        res = self.client.get(url_for(api.ResourceItem, type='supplies', id=1))
        assert res.status_code == 404


@pytest.mark.usefixtures('client_class', 'db', 'example_data_products')
class TestProducts:
    def test_get_from_list(self):
        res = self.client.get(url_for(api.ResourceList, type='products'))

        assert res.status_code == 200
        assert res.json['items'][0]['name']['en'] == 'Multilingual Product'
        assert res.json['items'][0]['details']['en'] == 'A product of society'
        assert res.json['items'][0]['ingredients'][0]['name']['en'] == (
            'Multilingual Ingredient')
        assert res.json['items'][1]['name']['en'] == 'English Product'
        assert res.json['items'][1]['details']['en'] == 'A product of English society'
        assert res.json['items'][1]['ingredients'][0]['name']['en'] == (
            'English Ingredient (probably Tea)')
        assert res.json['items'][2]['name']['de'] == 'Deutsches Produkt'
        assert res.json['items'][2]['details']['de'] == 'Faelscht Emissionsdaten'
        assert res.json['items'][2]['ingredients'][0]['name']['de'] == (
            'Deutscher Inhaltsstoff (wahrscheinlich Sauerkraut)')

        res = self.client.get(url_for(api.ResourceList, type='products', lang='de'))

        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Mehrsprachiges Produkt'
        assert res.json['items'][0]['details'] == 'Ein Produkt der Gesellschaft'
        assert res.json['items'][0]['ingredients'][0]['name'] == (
            'Mehrsprachige Ingredient')
        assert res.json['items'][1]['name'] == 'English Product'
        assert res.json['items'][1]['details'] == 'A product of English society'
        assert res.json['items'][1]['ingredients'][0]['name'] == (
            'English Ingredient (probably Tea)')
        assert res.json['items'][2]['name'] == 'Deutsches Produkt'
        assert res.json['items'][2]['details'] == 'Faelscht Emissionsdaten'
        assert res.json['items'][2]['ingredients'][0]['name'] == (
            'Deutscher Inhaltsstoff (wahrscheinlich Sauerkraut)')

        res = self.client.get(url_for(api.ResourceList, type='products', lang='it'))

        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Multilingual Product'
        assert res.json['items'][0]['details'] == 'A product of society'
        assert res.json['items'][0]['ingredients'][0]['name'] == (
            'Multilingual Ingredient')
        assert res.json['items'][1]['name'] == 'English Product'
        assert res.json['items'][1]['details'] == 'A product of English society'
        assert res.json['items'][1]['ingredients'][0]['name'] == (
            'English Ingredient (probably Tea)')
        assert res.json['items'][2]['name'] == 'Deutsches Produkt'
        assert res.json['items'][2]['details'] == 'Faelscht Emissionsdaten'
        assert res.json['items'][2]['ingredients'][0]['name'] == (
            'Deutscher Inhaltsstoff (wahrscheinlich Sauerkraut)')

    def test_get_item(self):
        res = self.client.get(url_for(api.ResourceItem, type='products', id=1))

        assert res.status_code == 200
        assert res.json['item']['name']['en'] == 'Multilingual Product'
        assert res.json['item']['details']['en'] == 'A product of society'
        assert res.json['item']['ingredients'][0]['name']['en'] == (
            'Multilingual Ingredient')

        res = self.client.get(url_for(api.ResourceItem, type='products',
                                      id=1, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Mehrsprachiges Produkt'
        assert res.json['item']['details'] == 'Ein Produkt der Gesellschaft'
        assert res.json['item']['ingredients'][0]['name'] == (
            'Mehrsprachige Ingredient')

        res = self.client.get(url_for(api.ResourceItem, type='products',
                                      id=1, lang='it'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Multilingual Product'
        assert res.json['item']['details'] == 'A product of society'
        assert res.json['item']['ingredients'][0]['name'] == (
            'Multilingual Ingredient')

    def test_post_to_list(self):
        res = self.client.post(
            url_for(api.ResourceList, type='products'),
            data=json.dumps({'name': {'en': 'POSTed Product',
                                      'de': 'Gepostetes Produkt'},
                             'details': {'en': 'POSTed details',
                                         'de': 'Gepostete Details'},
                             'ingredients': [{'weight': 1,
                                              'name': {'en': 'POSTed Ingredient',
                                                       'de': 'Gepostete Ingredient'}}]}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'POSTed Product'
        assert res.json['details']['en'] == 'POSTed details'
        assert res.json['ingredients'][0]['name']['en'] == 'POSTed Ingredient'

        res = self.client.get(url_for(api.ResourceItem, type='products',
                                      id=res.json['id'], lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Gepostetes Produkt'
        assert res.json['item']['details'] == 'Gepostete Details'
        assert res.json['item']['ingredients'][0]['name'] == 'Gepostete Ingredient'

    def test_put_item(self):
        res = self.client.put(
            url_for(api.ResourceItem, type='products', id=2),
            data=json.dumps({'name': {'en': 'PUTted Product',
                                      'de': 'Geputtetes Produkt'},
                             'details': {'en': 'PUTted details',
                                         'de': 'Geputtete Details'},
                             'ingredients': [{'weight': 100,
                                              'name': {'en': 'PUTted Ingredient',
                                                       'de': 'Geputtete Ingredient'}}]}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'PUTted Product'
        assert res.json['details']['en'] == 'PUTted details'
        assert res.json['ingredients'][0]['name']['en'] == 'PUTted Ingredient'

        res = self.client.get(url_for(api.ResourceItem, type='products',
                                      id=2, lang='de'))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'Geputtetes Produkt'
        assert res.json['item']['details'] == 'Geputtete Details'
        assert res.json['item']['ingredients'][0]['name'] == 'Geputtete Ingredient'

    def test_patch_item(self):
        res = self.client.patch(
            url_for(api.ResourceItem, type='products', id=3),
            data=json.dumps({'name': {'en': 'English only'},
                             'details': {'en': 'English details'},
                             'ingredients': [{'weight': 1000,
                                              'name': {'en': 'English Ingredient'}}]}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'English only'
        assert res.json['details']['en'] == 'English details'
        assert res.json['ingredients'][0]['name']['en'] == 'English Ingredient'

        res = self.client.get(url_for(api.ResourceItem, type='products',
                                      id=3, lang='de'))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'English only'
        assert res.json['item']['details'] == 'English details'
        assert res.json['item']['ingredients'][0]['name'] == 'English Ingredient'

    def test_delete_item(self):
        res = self.client.delete(url_for(api.ResourceItem, type='products', id=1))
        assert res.status_code == 204

        res = self.client.get(url_for(api.ResourceItem, type='products', id=1))
        assert res.status_code == 404


@pytest.mark.usefixtures('client_class', 'db', 'example_data_origin')
class TestOrigin:
    def test_get_from_list(self):
        res = self.client.get(url_for(api.ResourceList, type='origins'))

        assert res.status_code == 200
        assert res.json['items'][0]['name']['en'] == 'Austria'
        assert res.json['items'][0]['code'] == 'AT'
        assert res.json['items'][1]['name']['de'] == 'Deutschland'
        assert res.json['items'][1]['code'] == 'DE'
        assert res.json['items'][2]['name']['en'] == 'Great Britain'
        assert res.json['items'][2]['code'] == 'GB'

        res = self.client.get(url_for(api.ResourceList, type='origins', lang='de'))

        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Oesterreich'
        assert res.json['items'][0]['code'] == 'AT'
        assert res.json['items'][1]['name'] == 'Deutschland'
        assert res.json['items'][1]['code'] == 'DE'
        assert res.json['items'][2]['name'] == 'Great Britain'
        assert res.json['items'][2]['code'] == 'GB'

        res = self.client.get(url_for(api.ResourceList, type='origins', lang='it'))

        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Austria'
        assert res.json['items'][0]['code'] == 'AT'
        assert res.json['items'][1]['name'] == 'Deutschland'
        assert res.json['items'][1]['code'] == 'DE'
        assert res.json['items'][2]['name'] == 'Great Britain'
        assert res.json['items'][2]['code'] == 'GB'

    def test_get_item(self):
        res = self.client.get(url_for(api.ResourceItem, type='origins', id=1))

        assert res.status_code == 200
        assert res.json['item']['name']['en'] == 'Austria'
        assert res.json['item']['code'] == 'AT'

        res = self.client.get(url_for(api.ResourceItem, type='origins',
                                      id=1, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Oesterreich'
        assert res.json['item']['code'] == 'AT'

        res = self.client.get(url_for(api.ResourceItem, type='origins',
                                      id=1, lang='it'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Austria'
        assert res.json['item']['code'] == 'AT'

    def test_post_to_list(self):
        res = self.client.post(
            url_for(api.ResourceList, type='origins'),
            data=json.dumps({'name': {'en': 'POSTed Origin',
                                      'de': 'Gepostete Origin'},
                             'code': 'PO'}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'POSTed Origin'
        assert res.json['code'] == 'PO'

        res = self.client.get(url_for(api.ResourceItem, type='origins',
                                      id=res.json['id'], lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Gepostete Origin'
        assert res.json['item']['code'] == 'PO'

    def test_put_item(self):
        res = self.client.put(
            url_for(api.ResourceItem, type='origins', id=2),
            data=json.dumps({'name': {'en': 'PUTted Origin',
                                      'de': 'Geputtete Origin'},
                             'code': 'TO'}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'PUTted Origin'
        assert res.json['code'] == 'TO'

        res = self.client.get(url_for(api.ResourceItem, type='origins',
                                      id=2, lang='de'))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'Geputtete Origin'
        assert res.json['item']['code'] == 'TO'

    def test_patch_item(self):
        res = self.client.patch(
            url_for(api.ResourceItem, type='origins', id=3),
            data=json.dumps({'name': {'de': 'Vereinigtes Koenigreich'}}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['de'] == 'Vereinigtes Koenigreich'
        assert res.json['code'] == 'GB'

        res = self.client.get(url_for(api.ResourceItem, type='origins',
                                      id=3, lang='en'))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'Vereinigtes Koenigreich'
        assert res.json['item']['code'] == 'GB'

    def test_delete_item(self):
        res = self.client.delete(url_for(api.ResourceItem, type='origins', id=1))
        assert res.status_code == 204

        res = self.client.get(url_for(api.ResourceItem, type='origins', id=1))
        assert res.status_code == 404


@pytest.mark.usefixtures('client_class', 'db', 'example_data_criteria')
class TestCriteria:
    def test_get_from_list(self):
        res = self.client.get(url_for(api.ResourceList, type='criteria'))

        assert res.status_code == 200
        assert res.json['items'][0]['name']['en'] == 'Multilingual Criterion'
        assert res.json['items'][0]['details']['en'] == 'Multilingual details'
        assert res.json['items'][0]['category']['name']['en'] == 'Multilingual Criterion Category'
        assert res.json['items'][1]['name']['en'] == 'English Criterion'
        assert res.json['items'][1]['details']['en'] == 'English details'
        assert res.json['items'][1]['category']['name']['en'] == 'English Criterion Category'
        assert res.json['items'][2]['name']['de'] == 'Deutsches Criterion'
        assert res.json['items'][2]['details']['de'] == 'Deutsche Details'
        assert res.json['items'][2]['category']['name']['de'] == 'Deutsche Criterion Category'

        res = self.client.get(url_for(api.ResourceList, type='criteria', lang='de'))

        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Mehrsprachiges Criterion'
        assert res.json['items'][0]['details'] == 'Mehrsprachige Details'
        assert res.json['items'][0]['category']['name'] == 'Mehrsprachige Criterion Category'
        assert res.json['items'][1]['name'] == 'English Criterion'
        assert res.json['items'][1]['details'] == 'English details'
        assert res.json['items'][1]['category']['name'] == 'English Criterion Category'
        assert res.json['items'][2]['name'] == 'Deutsches Criterion'
        assert res.json['items'][2]['details'] == 'Deutsche Details'
        assert res.json['items'][2]['category']['name'] == 'Deutsche Criterion Category'

        res = self.client.get(url_for(api.ResourceList, type='criteria', lang='it'))

        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Multilingual Criterion'
        assert res.json['items'][0]['details'] == 'Multilingual details'
        assert res.json['items'][0]['category']['name'] == 'Multilingual Criterion Category'
        assert res.json['items'][1]['name'] == 'English Criterion'
        assert res.json['items'][1]['details'] == 'English details'
        assert res.json['items'][1]['category']['name'] == 'English Criterion Category'
        assert res.json['items'][2]['name'] == 'Deutsches Criterion'
        assert res.json['items'][2]['details'] == 'Deutsche Details'
        assert res.json['items'][2]['category']['name'] == 'Deutsche Criterion Category'

    def test_get_item(self):
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=1))

        assert res.status_code == 200
        assert res.json['item']['name']['en'] == 'Multilingual Criterion'
        assert res.json['item']['details']['en'] == 'Multilingual details'
        assert res.json['item']['category']['name']['en'] == 'Multilingual Criterion Category'

        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                                      id=1, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Mehrsprachiges Criterion'
        assert res.json['item']['details'] == 'Mehrsprachige Details'
        assert res.json['item']['category']['name'] == 'Mehrsprachige Criterion Category'

        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                                      id=1, lang='it'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Multilingual Criterion'
        assert res.json['item']['details'] == 'Multilingual details'
        assert res.json['item']['category']['name'] == 'Multilingual Criterion Category'

    def test_post_to_list(self):
        res = self.client.post(
            url_for(api.ResourceList, type='criteria'),
            data=json.dumps({'name': {'en': 'POSTed Criterion',
                                      'de': 'Gepostetes Criterion'},
                             'details': {'en': 'POSTed details',
                                         'de': 'Gepostete Details'},
                             'category': {'name': {'en': 'POSTed Category',
                                                   'de': 'Gepostete Category'}}}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'POSTed Criterion'
        assert res.json['details']['en'] == 'POSTed details'
        assert res.json['category']['name']['en'] == 'POSTed Category'

        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                                      id=res.json['id'], lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == 'Gepostetes Criterion'
        assert res.json['item']['details'] == 'Gepostete Details'
        assert res.json['item']['category']['name'] == 'Gepostete Category'

    def test_put_item(self):
        res = self.client.put(
            url_for(api.ResourceItem, type='criteria', id=2),
            data=json.dumps({'name': {'en': 'PUTted Criterion',
                                      'de': 'Geputtetes Criterion'},
                             'details': {'en': 'PUTted details',
                                         'de': 'Geputtete Details'},
                             'category': {'name': {'en': 'PUTted Category',
                                                   'de': 'Geputtete Category'}}}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'PUTted Criterion'
        assert res.json['details']['en'] == 'PUTted details'
        assert res.json['category']['name']['en'] == 'PUTted Category'

        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                                      id=2, lang='de'))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'Geputtetes Criterion'
        assert res.json['item']['details'] == 'Geputtete Details'
        assert res.json['item']['category']['name'] == 'Geputtete Category'

    def test_patch_item(self):
        res = self.client.patch(
            url_for(api.ResourceItem, type='criteria', id=3),
            data=json.dumps({'name': {'en': 'English only'},
                             'details': {'en': 'English details'},
                             'category': {'name': {'en': 'English Category'}}}),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['name']['en'] == 'English only'
        assert res.json['details']['en'] == 'English details'
        assert res.json['category']['name']['en'] == 'English Category'

        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                                      id=3, lang='de'))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'English only'
        assert res.json['item']['details'] == 'English details'
        assert res.json['item']['category']['name'] == 'English Category'

    def test_delete_item(self):
        res = self.client.delete(url_for(api.ResourceItem, type='criteria', id=1))
        assert res.status_code == 204

        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=1))
        assert res.status_code == 404


@pytest.mark.usefixtures('client_class', 'db', 'example_data_label_guide')
class TestLabelGuideUseCases:
    """Tests the label guide use cases, i.e.: GET /labels, GET/label?id=X"""
    def test_get_from_list(self):
        # Test default
        res = self.client.get(url_for(api.ResourceList, type='labels'))

        assert res.status_code == 200

        assert res.json['items'][0]['name']['en'] == Util.lbl1_name
        assert res.json['items'][0]['name']['de'] == Util.lbl1_name_de
        assert res.json['items'][0]['description']['en'] == Util.lbl1_description
        assert res.json['items'][0]['description']['de'] == Util.lbl1_description_de
        assert res.json['items'][1]['name']['en'] == Util.lbl2_name
        assert res.json['items'][1]['description']['en'] == Util.lbl2_description
        assert res.json['items'][2]['name']['de'] == Util.lbl3_name
        assert res.json['items'][2]['description']['de'] == Util.lbl3_description

        assert res.json['items'][0]['meets_criteria'][0]['explanation']['en'] == (
            Util.crit1_explanation)
        assert res.json['items'][0]['meets_criteria'][0]['explanation']['de'] == (
            Util.crit1_explanation_de)
        assert res.json['items'][1]['meets_criteria'][0]['explanation']['en'] == (
            Util.crit2_explanation)
        assert res.json['items'][2]['meets_criteria'][0]['explanation']['de'] == (
            Util.crit3_explanation)

        # Test German (data without German translation should revert to English)
        res = self.client.get(url_for(api.ResourceList, type='labels', lang='de'))

        assert res.status_code == 200

        assert res.json['items'][0]['name'] == Util.lbl1_name_de
        assert res.json['items'][0]['description'] == Util.lbl1_description_de
        assert res.json['items'][1]['name'] == Util.lbl2_name
        assert res.json['items'][1]['description'] == Util.lbl2_description
        assert res.json['items'][2]['name'] == Util.lbl3_name
        assert res.json['items'][2]['description'] == Util.lbl3_description

        assert res.json['items'][0]['meets_criteria'][0]['explanation'] == (
            Util.crit1_explanation_de)
        assert res.json['items'][1]['meets_criteria'][0]['explanation'] == Util.crit2_explanation
        assert res.json['items'][2]['meets_criteria'][0]['explanation'] == Util.crit3_explanation

        # Test Italian (no data, should revert to default)
        res = self.client.get(url_for(api.ResourceList, type='labels', lang='it'))

        assert res.status_code == 200

        assert res.json['items'][0]['name'] == Util.lbl1_name
        assert res.json['items'][0]['description'] == Util.lbl1_description
        assert res.json['items'][1]['name'] == Util.lbl2_name
        assert res.json['items'][1]['description'] == Util.lbl2_description
        assert res.json['items'][2]['name'] == Util.lbl3_name
        assert res.json['items'][2]['description'] == Util.lbl3_description

        assert res.json['items'][0]['meets_criteria'][0]['explanation'] == Util.crit1_explanation
        assert res.json['items'][1]['meets_criteria'][0]['explanation'] == Util.crit2_explanation
        assert res.json['items'][2]['meets_criteria'][0]['explanation'] == Util.crit3_explanation

    def test_get_single_item(self):
        # Test default
        res = self.client.get(url_for(api.ResourceItem, type='labels', id=1))

        assert res.status_code == 200
        assert res.json['item']['name']['en'] == Util.lbl1_name
        assert res.json['item']['name']['de'] == Util.lbl1_name_de
        assert res.json['item']['description']['en'] == Util.lbl1_description
        assert res.json['item']['description']['de'] == Util.lbl1_description_de
        assert res.json['item']['meets_criteria'][0]['explanation']['en'] == Util.crit1_explanation
        assert res.json['item']['meets_criteria'][0]['explanation']['de'] == (
            Util.crit1_explanation_de)

        # Test German
        res = self.client.get(url_for(api.ResourceItem, type='labels', id=1, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == Util.lbl1_name_de
        assert res.json['item']['description'] == Util.lbl1_description_de
        assert res.json['item']['meets_criteria'][0]['explanation'] == Util.crit1_explanation_de

        # Test Italian (no data, should revert to English)
        res = self.client.get(url_for(api.ResourceItem, type='labels', id=1, lang='it'))

        assert res.status_code == 200
        assert res.json['item']['name'] == Util.lbl1_name
        assert res.json['item']['description'] == Util.lbl1_description
        assert res.json['item']['meets_criteria'][0]['explanation'] == Util.crit1_explanation
