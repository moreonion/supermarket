import pytest
from supermarket import App

@pytest.fixture
def app():
    return App('supermarket', env='Testing')
