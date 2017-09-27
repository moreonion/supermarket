import pytest
import json
import supermarket.api as api

url_for = api.api.url_for


@pytest.mark.usefixtures('client_class', 'db', 'example_data_criteria', 'example_data_labels')
class TestLabelGuideUseCases:
    def test_labels_get(self):
        """Test whether we can receive name and description for labels and criteria
        in different languages."""
        res = self.client.get(url_for(api.ResourceList, type='labels'))
        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Testlabel'
        assert res.json['items'][0]['description'] == 'For exceptional testing.'
        assert {
            'explanation': 'Does the label improve testing for all of us?',
            'criterion': 4,
            'score': 100,
            'language': 'en'
            } in res.json['items'][0]['meets_criteria']

        res = self.client.get(url_for(api.ResourceList, type='labels',
                              lang='de'))
        assert res.status_code == 200
        assert res.json['items'][0]['name'] == 'Testerfuellung'
        assert res.json['items'][0]['description'] == 'Fuer grossartiges Testen.'
        assert {
            'explanation': 'Verbessert das Label testen fuer alle?',
            'criterion': 4,
            'score': 100,
            'language': 'de'
            } in res.json['items'][0]['meets_criteria']

    def test_label_get(self):
        """Test whether we can receive names and description in different languages
        for a single label."""
        res = self.client.get(url_for(api.ResourceItem, type='labels', id=1))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'Testlabel'
        assert res.json['item']['description'] == 'For exceptional testing.'

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=1,
                              lang='de'))
        assert res.status_code == 200
        assert res.json['item']['name'] == 'Testerfuellung'
        assert res.json['item']['description'] == 'Fuer grossartiges Testen.'


@pytest.mark.usefixtures('client_class', 'db', 'example_data_criteria')
class TestTranslatedJSON:
    # Criterion ID 1: Only English
    # Criterion ID 2: Only German
    # Criterion ID 3: Both English and German

    def test_criteria_details_en_get(self):
        """Tests whether we can receive details for criteria with English details."""

        # Check Criterion 1 with default language (en)
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=1))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'What is a question?'
        assert details['measures']['2'] == 'A phrase with an answer.'

        # Check Criterion 1 with English set specifically
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=1, lang='en'))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'What is a question?'
        assert details['measures']['2'] == 'A phrase with an answer.'

        # Check Criterion 1 with German set specifically (should result in
        # default language fields)
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=1, lang='de'))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'What is a question?'
        assert details['measures']['2'] == 'A phrase with an answer.'

    def test_criteria_details_de_get(self):
        """Tests whether we can receive details for criteria with German details."""
        # Check Criterion 2 with default language
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=2))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'Was ist eine Frage?'
        assert details['measures']['2'] == 'Ein Satz mit einer Antwort.'

        # Check Criterion 2 with English set specifically
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=2, lang='en'))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'Was ist eine Frage?'
        assert details['measures']['2'] == 'Ein Satz mit einer Antwort.'

        # Check Criterion 2 with German set specifically
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=2, lang='de'))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'Was ist eine Frage?'
        assert details['measures']['2'] == 'Ein Satz mit einer Antwort.'

    def test_criteria_details_de_en_get(self):
        """Tests whether we can receive details for criteria with German and
        English details."""
        # Check Criterion 3 with default language
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=3))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'What is a question?'
        assert details['measures']['2'] == 'A phrase with an answer.'

        # Check Criterion 3 with language set to English
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=3, lang='en'))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'What is a question?'
        assert details['measures']['2'] == 'A phrase with an answer.'

        # Check Criterion 3 with language set to German
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=3, lang='de'))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'Was ist eine Frage?'
        assert details['measures']['2'] == 'Ein Satz mit einer Antwort.'

        # Check Criterion 3 with language set to Italian
        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=3, lang='it'))
        details = res.json['item']['details']

        assert res.status_code == 200
        assert details['question'] == 'What is a question?'
        assert details['measures']['2'] == 'A phrase with an answer.'

    def test_criteria_details_post(self):
        """Test whether we can post a translated element to the list."""
        q_en = 'Can we post to the list?'
        q_de = 'Koennen wir auf Liste posten?'
        a_en = 'Posting works fine.'
        a_de = 'Posten funktioniert.'

        res = self.client.post(
            url_for(api.ResourceList, type='criteria'),
            data=json.dumps({
                'type': 'label',
                'name': 'Test post to list',
                'details': {
                    'question': [
                        {'value': q_en,
                         'lang': 'en'},
                        {'value': q_de,
                         'lang': 'de'}
                    ],
                    'measures': {
                        2: [
                            {'value': a_en,
                             'lang': 'en'},
                            {'value': a_de,
                             'lang': 'de'}
                        ]
                    }
                }
            }),
            content_type='application/json')

        assert res.status_code == 201
        # Check if response is in default language (en)
        assert res.json['details']['question'] == q_en
        assert res.json['details']['measures']['2'] == a_en

        created_id = res.json['id']
        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                              id=created_id))

        assert res.status_code == 200
        assert res.json['item']['details']['question'] == q_en
        assert res.json['item']['details']['measures']['2'] == a_en

        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                              id=created_id, lang='en'))

        assert res.status_code == 200
        assert res.json['item']['details']['question'] == q_en
        assert res.json['item']['details']['measures']['2'] == a_en

        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                              id=created_id, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['details']['question'] == q_de
        assert res.json['item']['details']['measures']['2'] == a_de

    def test_criteria_details_put_new(self):
        """Test whether we can create a new item via PUT."""
        q_en = 'Can we put to non-existant ID?'
        q_de = 'Koennen wir auf nicht-vorhandene ID putten?'
        a_en = 'Putting works fine.'
        a_de = 'Putten funktioniert.'

        res = self.client.put(
            url_for(api.ResourceItem, type='criteria', id=55),
            data=json.dumps({
                'type': 'label',
                'name': 'Test put to list',
                'details': {
                    'question': [
                        {'value': q_en,
                         'lang': 'en'},
                        {'value': q_de,
                         'lang': 'de'}
                    ],
                    'measures': {
                        2: [
                            {'value': a_en,
                             'lang': 'en'},
                            {'value': a_de,
                             'lang': 'de'}
                        ]
                    }
                }
            }),
            content_type='application/json')

        assert res.status_code == 201
        # Check if response is in default language (en)
        assert res.json['details']['question'] == q_en
        assert res.json['details']['measures']['2'] == a_en

        created_id = res.json['id']
        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                              id=created_id))

        assert res.status_code == 200
        assert res.json['item']['details']['question'] == q_en
        assert res.json['item']['details']['measures']['2'] == a_en

        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                              id=created_id, lang='en'))

        assert res.status_code == 200
        assert res.json['item']['details']['question'] == q_en
        assert res.json['item']['details']['measures']['2'] == a_en

        res = self.client.get(url_for(api.ResourceItem, type='criteria',
                              id=created_id, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['details']['question'] == q_de
        assert res.json['item']['details']['measures']['2'] == a_de

    def test_criteria_details_put_existing(self):
        """Test whether we can update a translated criterion via PUT."""
        res = self.client.put(
            url_for(api.ResourceItem, type='criteria', id=1),
            data=json.dumps(
                {'details':
                    {'question':
                        [{'value': 'Koennen wir updaten?',
                          'lang': 'de'}]
                     }
                 }
            ),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['details']['question'] == 'Koennen wir updaten?'

        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=1, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['details']['question'] == 'Koennen wir updaten?'

        res = self.client.put(
            url_for(api.ResourceItem, type='criteria', id=3),
            data=json.dumps(
                {'details':
                    {'question':
                        [{'value': 'Can we update?',
                          'lang': 'en'},
                         {'value': 'Koennen wir updaten?',
                          'lang': 'de'}],
                     'measures':
                     {2:
                         [{'value': 'Yes, we can!', 'lang': 'en'},
                          {'value': 'Ja, das koennen wir!', 'lang': 'de'}
                          ]}
                     }
                 }
            ),
            content_type='application/json')

        details = res.json['details']
        assert res.status_code == 201
        assert details['question'] == 'Can we update?'
        assert details['measures']['2'] == 'Yes, we can!'

        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=3, lang='de'))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'Koennen wir updaten?'
        assert details['measures']['2'] == 'Ja, das koennen wir!'

    def test_criteria_details_patch(self):
        """Test whether can update a translated criterion via PATCH."""
        res = self.client.patch(
            url_for(api.ResourceItem, type='criteria', id=2),
            data=json.dumps(
                {'details':
                    {'question':
                        [{'value': 'Can we patch?',
                          'lang': 'en'}]
                     }
                 }
            ),
            content_type='application/json')

        assert res.status_code == 201
        assert res.json['details']['question'] == 'Can we patch?'

        res = self.client.get(url_for(api.ResourceItem, type='criteria', id=2, lang='de'))

        details = res.json['item']['details']
        assert res.status_code == 200
        assert details['question'] == 'Was ist eine Frage?'
        assert details['measures']['2'] == 'Ein Satz mit einer Antwort.'
