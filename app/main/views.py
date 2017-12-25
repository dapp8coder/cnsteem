from flask import render_template, redirect, request, current_app, url_for, flash
from .forms import RegisterForm, PaymentForm
from . import main
from ..model import Order, User
from .. import db
import string
import random
import stripe
import os

stripe.api_key = os.environ['STRIPE_API_KEY']


def code_gen(size=16, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PaymentForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
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
                    'username': username,
                    'email': email
                }
            )
            order = Order(username=username, email=email, source_id=source.id)
            db.session.add(order)
            return redirect(source.redirect.url)
        except Exception:
            flash('支付跳转创建失败')
            return render_template('index.html', form=form)

    return render_template('index.html', form=form)


@main.route('/callback')
def callback():
    source_id = request.args.get('source', '')
    try:
        source = stripe.Source.retrieve(source_id)
        if source and source.status != "failed":
            return render_template("info.html", message="付款成功，请查看Email获取注册链接")
    except Exception:
        return render_template("info.html", message="付款失败")
    return render_template("info.html", message="付款失败")


@main.route('/webhook', methods=['POST'])
def webhook():
    payload = request.json

    if payload and payload['type'] == 'source.chargeable':
        try:
            data = payload['data']['object']
            charge = stripe.Charge.create(
                amount=data['amount'],
                currency=data['currency'],
                source=data['id'],
                description="Charged for %s" % data['metadata']['username']
            )
            if charge.status == 'succeeded':
                # Update the order info
                confirmed_code = code_gen(size=12)
                order = Order.query.filter_by(source_id=data['id']).first()
                order.charge_id = charge.id
                order.confirmed_code = confirmed_code
                db.session.add(order)
                # Send email TODO

                return 'Success'
        except Exception:
            return 'Failure'
    return 'Failure'


@main.route('/start/<string:code>', methods=['GET', 'POST'])
def register(code):
    order = Order.query.filter_by(confirmed_code=code).first_or_404()

    if order.created:
        return render_template('info.html', message="该用户已注册")

    form = RegisterForm()
    if form.validate_on_submit():
        # steem register TODO

        # update database
        order.created = True
        user = User(username=order.username, email=order.email)
        db.session.add(order)
        db.session.add(user)
        return render_template('info.html', message="注册成功")
    # generate register form
    form.email.data = order.email
    form.username.data = order.username
    form.password.data = code_gen(size=16)
    return render_template('index.html', form=form)
