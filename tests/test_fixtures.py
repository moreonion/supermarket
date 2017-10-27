import pytest

import supermarket.model as m
from fixtures import import_example_data


@pytest.mark.usefixtures('client_class', 'db')
class TestImportExampleData:
    def test_criteria_translations(self):
        import_example_data()
        for criterion in m.Criterion.query.all():
            assert 'de' in criterion.details
