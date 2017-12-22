from flask import Flask, redirect, url_for
from config import *
import stripe

app = Flask(__name__)
stripe.api_key = STRIPE_API_KEY


@app.route('/')
def index():
    return "hello word!"


@app.route('/pay', methods=['Post', 'Get'])
def pay():
    source = stripe.Source.create(
        type='alipay',
        amount=int(STRIPE_CHARGE_AMOUNT * 100),
        currency='usd',
        owner={
            'email': STRIPE_OWNER_EMAIL
        },
        redirect={
            'return_url': url_for('webhook', _external=True)
        },
        metadata={
            'username': 'test'
        }
    )

    return redirect(source.redirect.url)


@app.route('/webhook')
def webhook():
    return "Success"
