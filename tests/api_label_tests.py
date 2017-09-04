import pytest
import json
import supermarket.api as api

url_for = api.api.url_for
alpha_num = "abcdefghijklmnopqrstuvwxyz"
alpha_num += alpha_num.upper()
alpha_num += "0123456789"


@pytest.mark.usefixtures('client_class', 'db')
class TestLabelVerbs:
    def post_to_label(self, data):
        """
        POST request to labels.
        : returns The result of the request
        """
        return self.client.post(
            url_for(api.ResourceList, type='labels'),
            data=json.dumps(data),
            content_type='application/json'
            )

    def test_label_post(self):
        """ POST /labels """
        res = self.post_to_label({'name': 'Good stuff'})
        assert res.status_code == 201
