import pytest

import supermarket.api as api

url_for = api.api.url_for


@pytest.mark.usefixtures("client_class", "db", "example_data_brands")
class TestBrandQueryInclude:

    """Tests for the ?include=field1,field2,... GET parameter."""

    def test_general(self):
        """Check if we broke requests without any parameters."""
        url = url_for(api.ResourceItem, type="brands", id=1)
        res = self.client.get(url)

        assert res.status_code == 200
        assert res.json["item"]["name"] == "Clever"

        url = url_for(api.ResourceList, type="brands")
        res = self.client.get(url)

        assert res.status_code == 200
        assert res.json["items"][0]["name"] == "Clever"

    def test_single_field(self):
        """Check requesting a single field (products.name)."""
        url = url_for(api.ResourceItem, type="brands", id=1, include="products.name")
        res = self.client.get(url)

        assert res.status_code == 200
        assert "Chocolate chip cookies" in str(res.json["item"]["products"])

        url = url_for(api.ResourceList, type="brands", include="products.name")
        res = self.client.get(url)

        assert res.status_code == 200
        assert "Chocolate chip cookies" in str(res.json["items"][0]["products"])

    def test_multi_fields(self):
        """Check requesting multiple fields (products.id, products.name)."""
        url = url_for(api.ResourceItem, type="brands", id=1, include="products.name,products.id")
        res = self.client.get(url)

        assert res.status_code == 200
        assert "'id': 2" in str(res.json["item"]["products"])
        assert "Chocolate chip cookies" in str(res.json["item"]["products"])

        url = url_for(api.ResourceList, type="brands", include="products.name,products.id")
        res = self.client.get(url)

        assert res.status_code == 200
        assert "'id': 2" in str(res.json["items"][0]["products"])
        assert "Chocolate chip cookies" in str(res.json["items"][0]["products"])

    def test_all_fields(self):
        """Check whether requesting all fields works (products.all)"""
        url = url_for(api.ResourceItem, type="brands", id=1, include="products.all")
        res = self.client.get(url)

        assert res.status_code == 200
        assert "'id': 2" in str(res.json["item"]["products"])
        assert "Chocolate chip cookies" in str(res.json["item"]["products"])

        url = url_for(api.ResourceList, type="brands", include="products.all")
        res = self.client.get(url)

        assert res.status_code == 200
        assert "'id': 2" in str(res.json["items"][0]["products"])
        assert "Chocolate chip cookies" in str(res.json["items"][0]["products"])

    def test_empty(self):
        """Check whether the API can handle an empty include parameter."""
        url = url_for(api.ResourceItem, type="brands", id=1, include="")
        res = self.client.get(url)

        assert res.status_code == 200

        url = url_for(api.ResourceList, type="brands", include="")
        res = self.client.get(url)

        assert res.status_code == 200

    def test_whitespace(self):
        """Check whether the API can handle whitespace seperated fields."""
        url = url_for(api.ResourceItem, type="brands", id=1, include="products.adsf, products.id")
        res = self.client.get(url)

        assert res.status_code == 200
        assert "'id': 2" in str(res.json["item"]["products"])
        assert "Chocolate chip cookies" not in str(res.json["item"]["products"])

        url = url_for(api.ResourceList, type="brands", include="products.adsf, products.id")
        res = self.client.get(url)

        assert res.status_code == 200
        assert "'id': 2" in str(res.json["items"][0]["products"])
        assert "Chocolate chip cookies" not in str(res.json["items"][0]["products"])

    def test_invalid_args(self):
        """Check whether invalid field names trigger error messages."""
        url = url_for(api.ResourceItem, type="brands", id=1, include="products.adsf, products.id")
        res = self.client.get(url)

        assert res.status_code == 200
        assert "Unknown field `adsf`" in str(res.json["errors"])
        assert "'id': 2" in str(res.json["item"]["products"])
        assert "Chocolate chip cookies" not in str(res.json["item"]["products"])

        url = url_for(api.ResourceList, type="brands", include="products.adsf, products.id")
        res = self.client.get(url)

        assert res.status_code == 200
        assert "Unknown field `adsf`" in str(res.json["errors"])
        assert "'id': 2" in str(res.json["items"][0]["products"])
        assert "Chocolate chip cookies" not in str(res.json["items"][0]["products"])

    def test_null_value(self):
        """Check whether we can handle a NULL value in the Related Field."""
        url = url_for(api.ResourceItem, type="products", id=1)
        res = self.client.get(url)

        assert res.json["item"]["brand"] is None

        url = url_for(api.ResourceItem, type="products", id=1, include="brand.name")
        res = self.client.get(url)

        assert res.status_code == 200
        assert res.json["item"]["brand"] is None


@pytest.mark.usefixtures("client_class", "db", "example_data_labels")
class TestLabelQueryInclude:
    def test_include_resources_in_list(self):
        url = url_for(
            api.ResourceList,
            type="labels",
            sort="resources.id",
            include="resources.name,resources.id",
        )
        res = self.client.get(url)

        assert res.status_code == 200
        assert res.json["items"][0]["resources"][0]["name"]["en"] == "Testresource #1"
        assert res.json["items"][0]["resources"][1]["name"]["en"] == "Testresource #2"

    def test_include_resources(self):
        url = url_for(
            api.ResourceItem,
            type="labels",
            id=1,
            only="name,resources",
            include="resources.name,resources.id",
        )
        res = self.client.get(url)

        assert res.status_code == 200
        assert len(res.json["item"]["resources"]) == 2
        assert {"id": 1, "name": {"en": "Testresource #1"}} in res.json["item"]["resources"]
        assert {"id": 2, "name": {"en": "Testresource #2"}} in res.json["item"]["resources"]

    def test_include_hotspots(self):
        url = url_for(api.ResourceItem, type="labels", id=1, include="hotspots.name")
        res = self.client.get(url)

        assert res.status_code == 200
        assert res.json["item"]["hotspots"][0]["name"]["en"] == "Quality Assurance"

    def test_include_criteria(self):
        url = url_for(
            api.ResourceItem, type="labels", id=1, include="meets_criteria.criterion.name"
        )
        res = self.client.get(url)

        assert res.status_code == 200
        assert (
            res.json["item"]["meets_criteria"][0]["criterion"]["name"]["en"]
            == "The test improvement criterion"
        )

    def test_include_criteria_in_list(self):
        url = url_for(api.ResourceList, type="labels", include="meets_criteria.criterion.name")
        res = self.client.get(url)

        assert res.status_code == 200
        assert (
            res.json["items"][0]["meets_criteria"][0]["criterion"]["name"]["en"]
            == "The test improvement criterion"
        )
