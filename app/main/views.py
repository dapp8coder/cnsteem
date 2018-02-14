import os
import string
import secrets
import stripe
import requests
import hashlib
from flask import render_template, redirect, request, current_app as app, url_for, flash
from ..model import Order, User, SteemPower
from .. import db, email_tool
from . import steem_tool, main
from .forms import RegisterForm, PaymentForm, DelegateForm
from steem.converter import Converter
from steem.account import Account, Amount

stripe.api_key = os.environ['STRIPE_API_KEY']


def code_gen(size=16, chars=string.ascii_letters + string.digits):
    words = ['l', 'I', '0', 'O']
    chars = ''.join(c for c in chars if c not in words)
    return ''.join(secrets.choice(chars) for _ in range(size))


@main.route('/', methods=['GET', 'POST'])
def index():

    steem_power = SteemPower.query.filter_by(username=app.config['STEEM_REGISTER_CREATOR']).first()
    if steem_power and steem_power.sp < 20:
        return render_template('outoffund.html')

    form = PaymentForm()
    payment_amount = app.config['STRIPE_CHARGE_AMOUNT']
    form.amount.data = '$ ' + str(payment_amount)
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        try:
            source = stripe.Source.create(
                type='alipay',
                amount=int(payment_amount * 100),
                currency=app.config['STRIPE_CHARGE_CURRENCY'],
                owner={
                    'email': app.config['STRIPE_OWNER_EMAIL']
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
        except Exception as e:
            flash('支付跳转创建失败')
            app.logger.warning(str(e))
            return render_template('index.html', form=form)

    return render_template('index.html', form=form)


@main.route('/callback')
def callback():
    source_id = request.args.get('source', '')
    try:
        source = stripe.Source.retrieve(source_id)
        if source and source.status != "failed":
            return render_template("info.html", message="付款成功，请登录邮箱查看注册链接")
    except Exception as e:
        app.logger.warning(str(e))
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
                confirmed_code = code_gen(size=24)
                order = Order.query.filter_by(source_id=data['id']).first()
                order.charge_id = charge.id
                order.confirmed_code = confirmed_code
                db.session.add(order)
                # Send email
                if app.config['PRODUCTION']:
                    link = url_for('main.register', _external=True, code=confirmed_code)
                    status_code = email_tool.send_email(data['metadata']['email'], link)
                    app.logger.info('Email Status: %s:%s -> code: %s', data['metadata']['username'],
                                    data['metadata']['email'], status_code)
                return "Success"

        except Exception as e:
            app.logger.warning(str(e))
            return 'Failure'
    return 'Failure'


@main.route('/start/<string:code>', methods=['GET', 'POST'])
def register(code):
    order = Order.query.filter_by(confirmed_code=code).first_or_404()

    if order.created:
        return render_template('info.html', message="该用户已注册")

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # steem register
            if app.config['PRODUCTION']:
                steem_tool.create_account(
                    order.username,
                    delegation_fee_steem=app.config['STEEM_REGISTER_FEE'],
                    password=form.password.data,
                    creator=app.config['STEEM_REGISTER_CREATOR']
                )
                app.logger.info('Register Status: %s', order.username)
            # update database
            order.created = True
            user = User(username=order.username, email=order.email)
            db.session.add(order)
            db.session.add(user)
            return render_template('register_success.html')
        except Exception as e:
            app.logger.warning(str(e))
            return render_template('register_failure.html')
    # generate register form
    form.email.data = order.email
    form.username.data = order.username
    form.password.data = form.password.data if form.password.data else code_gen(size=40)
    return render_template('index.html', form=form)


@main.route('/delegate', methods=['GET', 'POST'])
def delegate():
    form = DelegateForm()
    if form.validate_on_submit():
        username = form.username.data
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('很抱歉，该账号未通过CNsteem.io注册，无法申请')
        elif Amount(Account(username)['received_vesting_shares']).amount > 4000:
            flash('很抱歉，该用户名已有足够带宽，请把机会让给他人')
        else:
            try:
                vests = '{} VESTS'.format(Converter().sp_to_vests(2))
                steem_tool.delegate_vesting_shares(username, vests, account=app.config['STEEM_REGISTER_CREATOR'])
                return render_template('info.html', message="申请成功")
            except Exception as e:
                app.logger.warning(str(e))
                return render_template('info.html', message='很抱歉，申请失败，请稍候再试或联系管理员')

    return render_template('delegate.html', form=form)


@main.route('/@<string:name>')
def blog(name):
    return render_template('blog.html', name=name)
