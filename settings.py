class Common:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ERROR_404_HELP = False


class TestingConfig(Common):
    TESTING = True,
    SECRET_KEY = b'Testing secret key'
    SQLALCHEMY_DATABASE_URI = 'postgresql:///supermarket_test'


class DevelopmentConfig(Common):
    SECRET_KEY = b'Development secret key'
    SQLALCHEMY_DATABASE_URI = "postgresql:///supermarket"
    SQLALCHEMY_RECORD_QUERIES = True
