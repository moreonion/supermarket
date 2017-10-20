class Common:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ERROR_404_HELP = False
    AUTH0_DOMAIN = 'moreonion.eu.auth0.com'
    AUTH0_API_AUDIENCE = 'supermarket-api'
    AUTH0_ENABLE = True


class TestingConfig(Common):
    TESTING = True
    SECRET_KEY = b'Testing secret key'
    SQLALCHEMY_DATABASE_URI = 'postgresql:///supermarket_test'


class DevelopmentConfig(Common):
    DEBUG = True
    AUTH0_ENABLE = False
    SECRET_KEY = b'Development secret key'
    SQLALCHEMY_DATABASE_URI = "postgresql:///supermarket"
    SQLALCHEMY_RECORD_QUERIES = True
