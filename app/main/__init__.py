from flask import Blueprint
from beem import Steem
import os

main = Blueprint('main', __name__)

steem_tool = Steem(keys=[os.environ['STEEM_ACTIVE_KEY']])

from . import views, errors