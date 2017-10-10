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
                                    "meets_criteria": [{"criterion": 1}],
                                    }),
                               content_type='application/json')

        assert res.status_code == 201
        assert res.json['name'] == Util.lbl4_name
        assert res.json['description'] == Util.lbl4_description
        id = res.json['id']

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=id))

        assert res.status_code == 200
        assert res.json['item']['name'] == Util.lbl4_name
        assert res.json['item']['description'] == Util.lbl4_description

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=id, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == Util.lbl4_name_de
        assert res.json['item']['description'] == Util.lbl4_description_de

        # What's our return value if we don't post an English value?
        res = self.client.post(url_for(api.ResourceList, type='labels'),
                               data=json.dumps(
                                   {"name": {"de": Util.lbl4_name_de},
                                    "description": {"de": Util.lbl4_description_de},
                                    "meets_criteria": [{"criterion": 3}],
                                    }),
                               content_type='application/json')

        assert res.status_code == 201
        assert res.json['name'] == Util.lbl4_name_de
        assert res.json['description'] == Util.lbl4_description_de

    def test_put_item(self):
        # Replace first label's data with new data
        res = self.client.put(url_for(api.ResourceItem, type='labels', id=1),
                              data=json.dumps(
                                  {"name": {"en": Util.lbl5_name,
                                            "de": Util.lbl5_name_de},
                                   "description": {
                                       "en": Util.lbl5_description,
                                       "de": Util.lbl5_description_de},
                                   "meets_criteria": [{"criterion": 1}],
                                   }),
                              content_type='application/json')

        assert res.status_code == 201
        assert res.json['name'] == Util.lbl5_name
        assert res.json['description'] == Util.lbl5_description
        assert res.json['meets_criteria'][0]['criterion'] == 1

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=1))

        assert res.status_code == 200
        assert res.json['item']['name'] == Util.lbl5_name
        assert res.json['item']['description'] == Util.lbl5_description
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
        assert res.json['name'] == Util.lbl6_name
        assert res.json['description'] == Util.lbl6_description
        assert res.json['meets_criteria'][0]['criterion'] == 1

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=3))

        assert res.status_code == 200
        assert res.json['item']['name'] == Util.lbl6_name
        assert res.json['item']['description'] == Util.lbl6_description
        assert res.json['item']['meets_criteria'][0]['criterion'] == 1

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=3, lang='de'))

        assert res.status_code == 200
        assert res.json['item']['name'] == Util.lbl3_name
        assert res.json['item']['description'] == Util.lbl3_description
        assert res.json['item']['meets_criteria'][0]['criterion'] == 1

        # Update the English values of the German & English label
        res = self.client.patch(url_for(api.ResourceItem, type='labels', id=1),
                                data=json.dumps(
                                    {"name": {"en": Util.lbl6_name},
                                     "description": {"en": Util.lbl6_description}}),
                                content_type='application/json')

        assert res.status_code == 201
        assert res.json['name'] == Util.lbl6_name
        assert res.json['description'] == Util.lbl6_description

    def test_delete_item(self):
        # Delete a whole item
        res = self.client.delete(url_for(api.ResourceItem, type='labels', id=1))
        assert res.status_code == 204

        res = self.client.get(url_for(api.ResourceItem, type='labels', id=1))
        assert res.status_code == 404


@pytest.mark.usefixtures('client_class', 'db', 'example_data_label_guide')
class TestLabelGuideUseCases:
    """Tests the label guide use cases, i.e.: GET /labels, GET/label?id=X"""
    def test_get_from_list(self):
        # Test default
        res = self.client.get(url_for(api.ResourceList, type='labels'))

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
        assert res.json['item']['name'] == Util.lbl1_name
        assert res.json['item']['description'] == Util.lbl1_description
        assert res.json['item']['meets_criteria'][0]['explanation'] == Util.crit1_explanation

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


# class TestLabelGuideUseCases:
#     def test_labels(self):
#         post_en = 'Test post to list'
#         post_de = 'Teste post auf die Liste'
#         name_de = 'Patch test in Deutsch'

#         res = self.client.post(
#             url_for(api.ResourceList, type='labels'),
#             data=json.dumps({
#                 'name': {'en': post_en},
#             }),
#             content_type='application/json')

#         assert res.status_code == 201
#         assert res.json['name'] == post_en

#         id = res.json['id']
#         res = self.client.patch(
#             url_for(api.ResourceItem, type='labels', id=id, lang='de'),
#             data=json.dumps({
#                 'name': {'de': name_de},
#             }),
#             content_type='application/json')

#         assert res.status_code == 201
#         assert res.json['name'] == name_de

#         res = self.client.get(url_for(api.ResourceItem, type='labels', id=id))
#         assert res.status_code == 200
#         assert res.json['item']['name'] == 'Test put to list'

#         res = self.client.get(url_for(api.ResourceItem, type='labels', id=id, lang='de'))
#         assert res.status_code == 200
#         assert res.json['item']['name'] == 'Teste ein put auf die Liste'

#         res = self.client.get(url_for(api.ResourceItem, type='labels', id=id, lang='it'))
#         assert res.status_code == 200
#         assert res.json['item']['name'] == 'Test put to list'

#         res = self.client.get(url_for(api.ResourceList, type='labels'))
#         assert res.status_code == 200
#         assert res.json['items'][0]['name'] == 'Test put to list'

#         res = self.client.get(url_for(api.ResourceList, type='labels', lang='de'))
#         assert res.status_code == 200
#         assert res.json['items'][0]['name'] == 'Teste ein put auf die Liste'

#         res = self.client.get(url_for(api.ResourceList, type='labels', lang='it'))
#         assert res.status_code == 200
#         assert res.json['items'][0]['name'] == 'Test put to list'

#     def test_criteria(self):
#         res = self.client.post(
#             url_for(api.ResourceList, type='labels'),
#             data=json.dumps({
#                 'name': {'en': 'A test label'},
#                 'meets_criteria': [
#                     {'explanation': {'en': 'Does the label improve testing?'},
#                      'criterion': {'name': 'My criterion'},
#                      'score': 100
#                      }
#                 ]
#             }),
#             content_type='application/json')

#         id = res.json['id']
#         assert res.status_code == 201
#         assert res.json['name'] == 'A test label'
#         assert res.json['meets_criteria'][0]['explanation']['en'] == (
#             'Does the label improve testing?')

#         res = self.client.get(url_for(api.ResourceItem, type='labels', id=id))
#         assert res.status_code == 200
#         assert res.json['item']['name'] == 'A test label'
#         assert res.json['item']['meets_criteria'][0]['explanation'] == (
#             'Does the label improve testing?')

# # @pytest.mark.usefixtures('client_class', 'db', 'example_data_criteria', 'example_data_labels')
# # class TestLabelGuideUseCases:
# #     def test_labels_get(self):
# #         """Test whether we can receive name and description for labels and criteria
# #         in different languages."""
# #         res = self.client.get(url_for(api.ResourceList, type='labels'))
# #         assert res.status_code == 200
# #         assert res.json['items'][0]['name'] == 'Testlabel'
# #         assert res.json['items'][0]['description'] == 'For exceptional testing.'
# #         assert {
# #             'explanation': 'Does the label improve testing for all of us?',
# #             'criterion': 4,
# #             'score': 100,
# #             'language': 'en'
# #             } in res.json['items'][0]['meets_criteria']

# #         res = self.client.get(url_for(api.ResourceList, type='labels',
# #                               lang='de'))
# #         assert res.status_code == 200
# #         assert res.json['items'][0]['name'] == 'Testerfuellung'
# #         assert res.json['items'][0]['description'] == 'Fuer grossartiges Testen.'
# #         assert {
# #             'explanation': 'Verbessert das Label testen fuer alle?',
# #             'criterion': 4,
# #             'score': 100,
# #             'language': 'de'
# #             } in res.json['items'][0]['meets_criteria']

# #         res = self.client.get(url_for(api.ResourceList, type='labels',
# #                               lang='it'))
# #         assert res.status_code == 200
# #         assert res.json['items'][0]['name'] == 'Testlabel'
# #         assert res.json['items'][0]['description'] == 'For exceptional testing.'
# #         assert {
# #             'explanation': 'Does the label improve testing for all of us?',
# #             'criterion': 4,
# #             'score': 100,
# #             'language': 'en'
# #             } in res.json['items'][0]['meets_criteria']

# #     def test_label_get(self):
# #         """Test whether we can receive names and description in different languages
# #         for a single label."""
# #         res = self.client.get(url_for(api.ResourceItem, type='labels', id=1))
# #         assert res.status_code == 200
# #         assert res.json['item']['name'] == 'Testlabel'
# #         assert res.json['item']['description'] == 'For exceptional testing.'
# #         assert {
# #             'explanation': 'Does the label improve testing for all of us?',
# #             'criterion': 4,
# #             'score': 100,
# #             'language': 'en'
# #             } in res.json['item']['meets_criteria']

# #         res = self.client.get(url_for(api.ResourceItem, type='labels', id=1,
# #                               lang='de'))
# #         assert res.status_code == 200
# #         assert res.json['item']['name'] == 'Testerfuellung'
# #         assert res.json['item']['description'] == 'Fuer grossartiges Testen.'
# #         assert {
# #             'explanation': 'Verbessert das Label testen fuer alle?',
# #             'criterion': 4,
# #             'score': 100,
# #             'language': 'de'
# #             } in res.json['item']['meets_criteria']

# #         res = self.client.get(url_for(api.ResourceItem, type='labels', id=2,
# #                               lang='de'))
# #         assert res.status_code == 200
# #         assert res.json['item']['name'] == 'German Name'
# #         assert res.json['item']['description'] == 'Only English description.'
# #         assert res.json['item']['language'] == 'mixed'


# # @pytest.mark.usefixtures('client_class', 'db', 'example_data_criteria')
# # class TestTranslatedJSON:
# #     # Criterion ID 1: Only English
# #     # Criterion ID 2: Only German
# #     # Criterion ID 3: Both English and German

# #     def test_criteria_details_en_get(self):
# #         """Tests whether we can receive details for criteria with English details."""

# #         # Check Criterion 1 with default language (en)
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=1))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'What is a question?'
# #         assert details['measures']['2'] == 'A phrase with an answer.'

# #         # Check Criterion 1 with English set specifically
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=1, lang='en'))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'What is a question?'
# #         assert details['measures']['2'] == 'A phrase with an answer.'

# #         # Check Criterion 1 with German set specifically (should result in
# #         # default language fields)
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=1, lang='de'))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'What is a question?'
# #         assert details['measures']['2'] == 'A phrase with an answer.'

# #     def test_criteria_details_de_get(self):
# #         """Tests whether we can receive details for criteria with German details."""
# #         # Check Criterion 2 with default language
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=2))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'Was ist eine Frage?'
# #         assert details['measures']['2'] == 'Ein Satz mit einer Antwort.'

# #         # Check Criterion 2 with English set specifically
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=2, lang='en'))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'Was ist eine Frage?'
# #         assert details['measures']['2'] == 'Ein Satz mit einer Antwort.'

# #         # Check Criterion 2 with German set specifically
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=2, lang='de'))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'Was ist eine Frage?'
# #         assert details['measures']['2'] == 'Ein Satz mit einer Antwort.'

# #     def test_criteria_details_de_en_get(self):
# #         """Tests whether we can receive details for criteria with German and
# #         English details."""
# #         # Check Criterion 3 with default language
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=3))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'What is a question?'
# #         assert details['measures']['2'] == 'A phrase with an answer.'

# #         # Check Criterion 3 with language set to English
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=3, lang='en'))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'What is a question?'
# #         assert details['measures']['2'] == 'A phrase with an answer.'

# #         # Check Criterion 3 with language set to German
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=3, lang='de'))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'Was ist eine Frage?'
# #         assert details['measures']['2'] == 'Ein Satz mit einer Antwort.'

# #         # Check Criterion 3 with language set to Italian
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=3, lang='it'))
# #         details = res.json['item']['details']

# #         assert res.status_code == 200
# #         assert details['question'] == 'What is a question?'
# #         assert details['measures']['2'] == 'A phrase with an answer.'

# #     def test_criteria_details_post(self):
# #         """Test whether we can post a translated element to the list."""
# #         q_en = 'Can we post to the list?'
# #         q_de = 'Koennen wir auf Liste posten?'
# #         a_en = 'Posting works fine.'
# #         a_de = 'Posten funktioniert.'

# #         res = self.client.post(
# #             url_for(api.ResourceList, type='criteria'),
# #             data=json.dumps({
# #                 'type': 'label',
# #                 'name': 'Test post to list',
# #                 'details': {
# #                     'question': [
# #                         {'value': q_en,
# #                          'lang': 'en'},
# #                         {'value': q_de,
# #                          'lang': 'de'}
# #                     ],
# #                     'measures': {
# #                         2: [
# #                             {'value': a_en,
# #                              'lang': 'en'},
# #                             {'value': a_de,
# #                              'lang': 'de'}
# #                         ]
# #                     }
# #                 }
# #             }),
# #             content_type='application/json')

# #         assert res.status_code == 201
# #         # Check if response is in default language (en)
# #         assert res.json['details']['question'] == q_en
# #         assert res.json['details']['measures']['2'] == a_en

# #         created_id = res.json['id']
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria',
# #                               id=created_id))

# #         assert res.status_code == 200
# #         assert res.json['item']['details']['question'] == q_en
# #         assert res.json['item']['details']['measures']['2'] == a_en

# #         res = self.client.get(url_for(api.ResourceItem, type='criteria',
# #                               id=created_id, lang='en'))

# #         assert res.status_code == 200
# #         assert res.json['item']['details']['question'] == q_en
# #         assert res.json['item']['details']['measures']['2'] == a_en

# #         res = self.client.get(url_for(api.ResourceItem, type='criteria',
# #                               id=created_id, lang='de'))

# #         assert res.status_code == 200
# #         assert res.json['item']['details']['question'] == q_de
# #         assert res.json['item']['details']['measures']['2'] == a_de

# #     def test_criteria_details_put_new(self):
# #         """Test whether we can create a new item via PUT."""
# #         q_en = 'Can we put to non-existant ID?'
# #         q_de = 'Koennen wir auf nicht-vorhandene ID putten?'
# #         a_en = 'Putting works fine.'
# #         a_de = 'Putten funktioniert.'

# #         res = self.client.put(
# #             url_for(api.ResourceItem, type='criteria', id=55),
# #             data=json.dumps({
# #                 'type': 'label',
# #                 'name': 'Test put to list',
# #                 'details': {
# #                     'question': [
# #                         {'value': q_en,
# #                          'lang': 'en'},
# #                         {'value': q_de,
# #                          'lang': 'de'}
# #                     ],
# #                     'measures': {
# #                         2: [
# #                             {'value': a_en,
# #                              'lang': 'en'},
# #                             {'value': a_de,
# #                              'lang': 'de'}
# #                         ]
# #                     }
# #                 }
# #             }),
# #             content_type='application/json')

# #         assert res.status_code == 201
# #         # Check if response is in default language (en)
# #         assert res.json['details']['question'] == q_en
# #         assert res.json['details']['measures']['2'] == a_en

# #         created_id = res.json['id']
# #         res = self.client.get(url_for(api.ResourceItem, type='criteria',
# #                               id=created_id))

# #         assert res.status_code == 200
# #         assert res.json['item']['details']['question'] == q_en
# #         assert res.json['item']['details']['measures']['2'] == a_en

# #         res = self.client.get(url_for(api.ResourceItem, type='criteria',
# #                               id=created_id, lang='en'))

# #         assert res.status_code == 200
# #         assert res.json['item']['details']['question'] == q_en
# #         assert res.json['item']['details']['measures']['2'] == a_en

# #         res = self.client.get(url_for(api.ResourceItem, type='criteria',
# #                               id=created_id, lang='de'))

# #         assert res.status_code == 200
# #         assert res.json['item']['details']['question'] == q_de
# #         assert res.json['item']['details']['measures']['2'] == a_de

# #     def test_criteria_details_put_existing(self):
# #         """Test whether we can update a translated criterion via PUT."""
# #         res = self.client.put(
# #             url_for(api.ResourceItem, type='criteria', id=1),
# #             data=json.dumps(
# #                 {'details':
# #                     {'question':
# #                         [{'value': 'Koennen wir updaten?',
# #                           'lang': 'de'}]
# #                      }
# #                  }
# #             ),
# #             content_type='application/json')

# #         assert res.status_code == 201
# #         assert res.json['details']['question'] == 'Koennen wir updaten?'

# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=1, lang='de'))

# #         assert res.status_code == 200
# #         assert res.json['item']['details']['question'] == 'Koennen wir updaten?'

# #         res = self.client.put(
# #             url_for(api.ResourceItem, type='criteria', id=3),
# #             data=json.dumps(
# #                 {'details':
# #                     {'question':
# #                         [{'value': 'Can we update?',
# #                           'lang': 'en'},
# #                          {'value': 'Koennen wir updaten?',
# #                           'lang': 'de'}],
# #                      'measures':
# #                      {2:
# #                          [{'value': 'Yes, we can!', 'lang': 'en'},
# #                           {'value': 'Ja, das koennen wir!', 'lang': 'de'}
# #                           ]}
# #                      }
# #                  }
# #             ),
# #             content_type='application/json')

# #         details = res.json['details']
# #         assert res.status_code == 201
# #         assert details['question'] == 'Can we update?'
# #         assert details['measures']['2'] == 'Yes, we can!'

# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=3, lang='de'))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'Koennen wir updaten?'
# #         assert details['measures']['2'] == 'Ja, das koennen wir!'

# #     def test_criteria_details_patch(self):
# #         """Test whether can update a translated criterion via PATCH."""
# #         res = self.client.patch(
# #             url_for(api.ResourceItem, type='criteria', id=2),
# #             data=json.dumps(
# #                 {'details':
# #                     {'question':
# #                         [{'value': 'Can we patch?',
# #                           'lang': 'en'}]
# #                      }
# #                  }
# #             ),
# #             content_type='application/json')

# #         assert res.status_code == 201
# #         assert res.json['details']['question'] == 'Can we patch?'

# #         res = self.client.get(url_for(api.ResourceItem, type='criteria', id=2, lang='de'))

# #         details = res.json['item']['details']
# #         assert res.status_code == 200
# #         assert details['question'] == 'Was ist eine Frage?'
# #         assert details['measures']['2'] == 'Ein Satz mit einer Antwort.'
