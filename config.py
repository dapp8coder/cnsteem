import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STRIPE_CHARGE_AMOUNT = 1.25
    STRIPE_CHARGE_CURRENCY = 'usd'
    STRIPE_CHARGE_DESCRIPTION = 'Steem 注册'
    STRIPE_OWNER_EMAIL = "cnsteem@gmail.com"
    STEEM_REGISTER_CREATOR = "cnsteem"
    STEEM_REGISTER_FEE = "0.2 STEEM"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
