import os

from dotenv import load_dotenv

load_dotenv()

class Config(object):
    TESTING = False
    DEBUG = True
    DATABASE_URI = 'postgresql+psycopg2://postgres:example@postgres:5432/matchataxa'
    MAX_CONTENT_LENGTH = 16 * 1000 * 1000 # 16MB, 1024*1024?

    SECRET_KEY = 'no secret'

    WEB_ENV = os.getenv('WEB_ENV')

class ProductionConfig(Config):
    SECRET_KEY = os.getenv('SECRET_KEY')

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

