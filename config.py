import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STRIPE_CHARGE_AMOUNT = 2.00
    STRIPE_CHARGE_CURRENCY = 'usd'
    PAYSAPI_CHARGE_AMOUNT = 10.00
    STRIPE_CHARGE_DESCRIPTION = 'Steem 注册'
    STRIPE_OWNER_EMAIL = "cnsteem@gmail.com"
    STEEM_REGISTER_CREATOR = "cnsteem"
    STEEM_REGISTER_FEE = "0.2 STEEM"
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    LOG_FILE_NAME = 'cnsteem.log'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    LOGGING_REQUESTS = False
    DEBUG = True


class TestingConfig(Config):
    LOGGING_REQUESTS = False
    TESTING = True


class ProductionConfig(Config):
    LOGGING_REQUESTS = True
    PRODUCTION = True
    JOBS = [
        {
            'id': 'job1',
            'func': 'app.main.scheduler:update_sp',
            'trigger': 'interval',
            'seconds': 7200
        }
    ]


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
