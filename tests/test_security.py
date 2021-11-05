import json

import pytest

import supermarket.api as api
from supermarket.api import resources

url_for = api.api.url_for
auth_header = {"authorization": "Bearer notarealbearertokenofcourse"}


@pytest.mark.usefixtures("client_class", "db")
class TestUnauthorizedAccess:
    def test_no_bearer(self):
        for resource in resources:
            res = self.client.post(
                url_for(api.ResourceList, type=resource),
                data=json.dumps({"random": "data"}),
                content_type="application/json",
            )

            assert res.status_code == 401
            assert res.json["message"] == "Authorization header is expected."

            res = self.client.put(
                url_for(api.ResourceItem, type=resource, id=1),
                data=json.dumps({"random": "data"}),
                content_type="application/json",
            )

            assert res.status_code == 401
            assert res.json["message"] == "Authorization header is expected."

            res = self.client.patch(
                url_for(api.ResourceItem, type=resource, id=1),
                data=json.dumps({"random": "data"}),
                content_type="application/json",
            )

            assert res.status_code == 401
            assert res.json["message"] == "Authorization header is expected."

            res = self.client.delete(url_for(api.ResourceItem, type=resource, id=1))

            assert res.status_code == 401
            assert res.json["message"] == "Authorization header is expected."

    def test_wrong_header(self):
        header = {"authorization": "NOT a bearer token"}
        for resource in resources:
            res = self.client.post(
                url_for(api.ResourceList, type=resource),
                data=json.dumps({"random": "data"}),
                headers=header,
                content_type="application/json",
            )

            assert res.status_code == 401
            assert res.json["message"] == "Authorization header must start with Bearer."

            res = self.client.put(
                url_for(api.ResourceItem, type=resource, id=1),
                data=json.dumps({"random": "data"}),
                headers=header,
                content_type="application/json",
            )

            assert res.status_code == 401
            assert res.json["message"] == "Authorization header must start with Bearer."

            res = self.client.patch(
                url_for(api.ResourceItem, type=resource, id=1),
                data=json.dumps({"random": "data"}),
                headers=header,
                content_type="application/json",
            )

            assert res.status_code == 401
            assert res.json["message"] == "Authorization header must start with Bearer."

            res = self.client.delete(url_for(api.ResourceItem, type=resource, id=1), headers=header)

            assert res.status_code == 401
            assert res.json["message"] == "Authorization header must start with Bearer."
