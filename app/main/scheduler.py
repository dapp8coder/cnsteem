from .. import apscheduler, db
from ..model import SteemPower
from flask import current_app as app
from steem.converter import Converter
from steem.account import Account, Amount


def update_sp():
    with apscheduler.app.app_context():
        username = app.config['STEEM_REGISTER_CREATOR']
        acc = Account(username)
        amount = Converter().vests_to_sp(
            Amount(acc['vesting_shares']).amount - Amount(acc['delegated_vesting_shares']).amount)
        steem_power = SteemPower.query.filter_by(username=username).first()
        if not steem_power:
            steem_power = SteemPower(username=username, sp=amount)
        else:
            steem_power.sp = amount
        db.session.add(steem_power)
