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
    API_URL = os.getenv('API_URL')
    TAICOL_TOKEN = os.getenv('TAICOL_TOKEN')
    TAICOL_API = os.getenv('TAICOL_API')
    TAIEOL_TOKEN = os.getenv('TAIEOL_TOKEN')

    AWS_SES_SOURCE = os.getenv('AWS_SES_SOURCE')
    AWS_SES_REGION_NAME = os.getenv('AWS_SES_REGION_NAME')
    AWS_SES_ACCESS_KEY = os.getenv('AWS_SES_ACCESS_KEY')
    AWS_SES_SECRET_ACCESS_KEY = os.getenv('AWS_SES_SECRET_ACCESS_KEY')

class ProductionConfig(Config):
    SECRET_KEY = os.getenv('SECRET_KEY')

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

