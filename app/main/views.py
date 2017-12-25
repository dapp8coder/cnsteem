from flask import render_template, redirect, request, current_app, url_for
from .forms import RegisterForm
from . import main

import string
import random
import stripe
import os

stripe.api_key = os.environ['STRIPE_API_KEY']


def pw_gen(size=16, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


@main.route('/', methods=['GET', 'POST'])
def index():
    form = RegisterForm()
    if not form.password.data:
        form.password.data = pw_gen()

    if form.validate_on_submit():
        try:
            source = stripe.Source.create(
                type='alipay',
                amount=int(current_app.config['STRIPE_CHARGE_AMOUNT'] * 100),
                currency=current_app.config['STRIPE_CHARGE_CURRENCY'],
                owner={
                    'email': current_app.config['STRIPE_OWNER_EMAIL']
                },
                redirect={
                    'return_url': url_for('main.callback', _external=True)
                },
                metadata={
                    'username': form.username.data,
                    'email': form.email.data
                }
            )
            return redirect(source.redirect.url)
        except Exception as e:
            print(e)
            return render_template('404.html')

    return render_template('index.html', form=form)


@main.route('/callback')
def callback():
    source_id = request.args.get('source', '')

    source = stripe.Source.retrieve(source_id)

    if source and source.status == "chargeable":
        return "Register Success"

    return "Failure"


@main.route('/webhook')
def webhook():
    pass
