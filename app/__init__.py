import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_apscheduler import APScheduler
from config import config
import logging
import logging.handlers

db = SQLAlchemy()
bootstrap = Bootstrap()
apscheduler = APScheduler()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    bootstrap.init_app(app)
    db.init_app(app)
    apscheduler.init_app(app)
    apscheduler.start()
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    if app.config['LOGGING_REQUESTS']:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.handlers.RotatingFileHandler('logs/%s' % app.config['LOG_FILE_NAME'], maxBytes=102400,
                                                            backupCount=10)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s '))
        from .logger import logger as logger_blueprint
        app.register_blueprint(logger_blueprint)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    return app
