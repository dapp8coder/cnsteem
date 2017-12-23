from flask import Flask, url_for, request
from config import *
from steem import Steem
from helper import *
import stripe

app = Flask(__name__)
s = Steem()
stripe.api_key = STRIPE_API_KEY


@app.route('/')
def index():
    return "hello word!"


@app.route('/pay', methods=['Post'])
def pay():
    payload = request.json

    username = payload['username']
    email = payload['email']
    confirmed_email = payload['confirmed_email']

    user = s.get_account(username)
    if user:
        return build_error_response(msg='%s has already registered' % username)

    if email != confirmed_email:
        return build_error_response(msg="Email doesn't match")

    # save the order into database

    source = stripe.Source.create(
        type='alipay',
        amount=int(STRIPE_CHARGE_AMOUNT * 100),
        currency=STRIPE_CHARGE_CURRENCY,
        owner={
            'email': STRIPE_OWNER_EMAIL
        },
        redirect={
            'return_url': url_for('paid_callback', _external=True)
        },
        metadata={
            'username': username,
            'email': email
        }
    )
    print(source)
    data = {'redirect_url': source.redirect.url}
    return build_success_response(data=data)


@app.route('/callback')
def paid_callback():
    source_id = request.args.get('source', '')
    source = stripe.Source.retrieve(source_id)

    print(source)
    if source and source.status == "chargeable":
        return build_success_response(msg="Register Success")

    return build_error_response(msg="Failure")


@app.route('/webhook')
def webhook():

    payload = request.json

    print(payload)
    # verify the payment

    # register the steem account

    # save the user into database
    return "Success"


@app.errorhandler(401)
def auth_error(e):
    return unauthorized('Authentication Error')


@app.errorhandler(404)
def not_found_error(e):
    return not_found('Invalid URL')


@app.errorhandler(405)
def method_not_allowed_error(e):
    return not_allowed()


@app.errorhandler(500)
def internal_error(e):
    return internal_server_error()
