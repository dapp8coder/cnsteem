from flask import Blueprint, request
from flask import current_app as app
logger = Blueprint('logger', __name__)


@logger.before_app_request
def before_request():
    pass


@logger.after_app_request
def after_request(response):
    app.logger.info('[{0}] {1} {2}'.format(request.method, response.status, request.path))
    return response