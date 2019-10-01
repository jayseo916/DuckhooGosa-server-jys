class Base(object):
    APP_NAME = 'Duck_API_Server'
    TESTING = True
    DEBUG = True
    DATABASE_NAME = 'NONE'


class DevelopmentConfig(Base):
    DEBUG = True
    TESTING = True
    DATABASE_NAME = 'duckdevdb'
    CLIENT_HOST = 'http://localhost:3000'


class TestConfig(Base):
    DEBUG = True
    TESTING = True
    DATABASE_NAME = 'ducktestdb'
    CLIENT_HOST = 'http://duckhoo.site'


class ProductionConfig(Base):
    DEBUG = False
    DATABASE_NAME = 'duckproductiondb'
    CLIENT_HOST = 'http://duckhoo.site'
