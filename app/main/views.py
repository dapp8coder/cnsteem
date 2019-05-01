import os
import string
import secrets
import stripe
import hashlib
from datetime import date, timedelta
from flask import render_template, redirect, request, current_app as app, url_for, flash
from ..model import Order, User, SteemPower
from .. import db, email_tool, slack_tool
from . import steem_tool, main
from .forms import RegisterForm, PaymentForm, PaysAPIForm, VmqAPIForm

stripe.api_key = os.environ['STRIPE_API_KEY']


def code_gen(size=16, chars=string.ascii_letters + string.digits):
    words = ['l', 'I', '0', 'O']
    chars = ''.join(c for c in chars if c not in words)
    return ''.join(secrets.choice(chars) for _ in range(size))


@main.route('/test', methods=['GET', 'POST'])
def index():
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


@main.route('/info', methods=['GET'])
def my_info():
    today = date.today()
    yesterday = date.today() - timedelta(1)
    total_count = User.query.count()
    yesterday_count = User.query.filter(User.create_time < today, User.create_time > yesterday).count()
    today_count = User.query.filter(User.create_time > today).count()

    count = {'total': total_count, 'yesterday': yesterday_count, 'today': today_count}
    return render_template('stats.html', count=count)


@main.route('/faq')
def faq():
    return render_template('faq.html')


@main.route('/@<string:name>')
def blog(name):
    return render_template('blog.html', name=name)


@main.route('/pays', methods=['GET', 'POST'])
def pays_index():
    steem_power = SteemPower.query.filter_by(username=app.config['STEEM_REGISTER_CREATOR']).first()
    if steem_power and steem_power.sp < 20:
        return render_template('outoffund.html')

    form = PaymentForm()
    payment_amount = app.config['PAYSAPI_CHARGE_AMOUNT']
    form.amount.data = '￥ ' + str(payment_amount) + '元'
    if form.validate_on_submit():
        try:
            uid = os.environ['PAYSAPI_UID']
            token = os.environ['PAYSAPI_TOKEN']
            username = form.username.data
            email = form.email.data
            price = payment_amount
            istype = 1 if form.submit.data else 2  # 1 means alipay, 2 means wepay
            notify_url = url_for('main.pays_webhook', _external=True, _scheme='https')
            return_url = url_for('main.pays_callback', _external=True)
            orderid = 'pays_' + code_gen(size=16)
            orderuid = username
            key = str(istype) + notify_url + orderid + orderuid + str(price) + return_url + token + uid
            key = hashlib.md5(key.encode('utf-8')).hexdigest()

            new_form = PaysAPIForm()
            new_form.username.data = username
            new_form.email.data = email
            new_form.uid.data = uid
            new_form.price.data = price
            new_form.istype.data = istype
            new_form.notify_url.data = notify_url
            new_form.return_url.data = return_url
            new_form.orderid.data = orderid
            new_form.orderuid.data = orderuid
            new_form.key.data = key

            order = Order(username=username, email=email, source_id=orderid)
            db.session.add(order)
            return render_template('pay.html', form=new_form)
        except Exception as e:
            flash('支付跳转创建失败，请稍候再试')
            app.logger.warning(str(e))
            return render_template('index.html', form=form)

    return render_template('index.html', form=form)


@main.route('/pays/callback')
def pays_callback():
    order_id = request.args.get('orderid', '')
    try:
        if order_id:
            return render_template("info.html", message="付款成功，请登录邮箱查看注册链接")
    except Exception as e:
        app.logger.warning(str(e))
        return render_template("info.html", message="付款失败")
    return render_template("info.html", message="付款失败")


@main.route('/pays/webhook', methods=['POST'])
def pays_webhook():
    paysapi_id = request.form['paysapi_id']
    orderid = request.form['orderid']
    price = request.form['price']
    realprice = request.form['realprice']
    orderuid = request.form['orderuid']
    key = request.form['key']
    token = os.environ['PAYSAPI_TOKEN']

    correct_key = orderid + orderuid + paysapi_id + price + realprice + token
    correct_key = hashlib.md5(correct_key.encode('utf-8')).hexdigest()
    if key == correct_key:
        try:
            # Update the order info
            confirmed_code = code_gen(size=24)
            order = Order.query.filter_by(source_id=orderid).first()
            order.charge_id = paysapi_id
            order.confirmed_code = confirmed_code
            db.session.add(order)
            # Send email
            if 'PRODUCTION' in app.config and app.config['PRODUCTION']:
                link = url_for('main.register', _external=True, _scheme='https', code=confirmed_code)
                status_code = email_tool.send_email(order.email, link)
                app.logger.info('Email Status: %s:%s -> code: %s', order.username, order.email, status_code)
                slack_tool.send_to_slack(order.username, order.email, confirmed_code)
            return "Success", 200

        except Exception as e:
            app.logger.warning(str(e))
            return 'Exception', 404
    return 'Failure', 404


@main.route('/', methods=['GET', 'POST'])
def vmq_index():
    steem_power = SteemPower.query.filter_by(username=app.config['STEEM_REGISTER_CREATOR']).first()
    if steem_power and steem_power.sp < 20:
        return render_template('outoffund.html')

    form = PaymentForm()
    payment_amount = app.config['PAYSAPI_CHARGE_AMOUNT']
    form.amount.data = '￥ ' + str(payment_amount) + '元'
    if form.validate_on_submit():
        try:
            token = os.environ['VMQ_TOKEN']
            username = form.username.data
            email = form.email.data
            price = payment_amount
            type = 2 if form.submit.data else 1  # 2 means alipay, 1 means wepay
            payId = 'vkm_' + code_gen(size=16)
            param = username
            key = payId + param + str(type) + str(price) + token
            sign = hashlib.md5(key.encode('utf-8')).hexdigest()

            new_form = VmqAPIForm()
            new_form.username.data = username
            new_form.email.data = email

            new_form.payId.data = payId
            new_form.type.data = type
            new_form.price.data = price
            new_form.sign.data = sign
            new_form.param.data = param
            new_form.isHtml.data = 1

            order = Order(username=username, email=email, source_id=payId)
            db.session.add(order)
            return render_template('vkm.html', form=new_form)
        except Exception as e:
            flash('支付跳转创建失败，请稍候再试')
            app.logger.warning(str(e))
            return render_template('index.html', form=form)

    return render_template('index.html', form=form)


@main.route('/vmq/callback')
def vmq_callback():
    payId = request.args.get('payId', '')
    try:
        if payId:
            return render_template("info.html", message="付款成功，请登录邮箱查看注册链接")
    except Exception as e:
        app.logger.warning(str(e))
        return render_template("info.html", message="付款失败")
    return render_template("info.html", message="付款失败")


@main.route('/vmq/webhook', methods=['GET'])
def vmq_webhook():
    payId = request.args['payId']
    param = request.args['param']
    price = request.args['price']
    reallyPrice = request.args['reallyPrice']
    type = request.args['type']
    sign = request.args['sign']
    token = os.environ['VMQ_TOKEN']

    correct_key = payId + param + str(type) + str(price) + str(reallyPrice) + token
    correct_key = hashlib.md5(correct_key.encode('utf-8')).hexdigest()
    if sign == correct_key:
        try:
            # Update the order info
            confirmed_code = code_gen(size=24)
            order = Order.query.filter_by(source_id=payId).first()
            order.charge_id = payId
            order.confirmed_code = confirmed_code
            db.session.add(order)
            # Send email
            if 'PRODUCTION' in app.config and app.config['PRODUCTION']:
                link = url_for('main.register', _external=True, _scheme='https', code=confirmed_code)
                status_code = email_tool.send_email(order.email, link)
                app.logger.info('Email Status: %s:%s -> code: %s', order.username, order.email, status_code)
                slack_tool.send_to_slack(order.username, order.email, confirmed_code)
            return "success", 200

        except Exception as e:
            app.logger.warning(str(e))
            return 'Exception', 404
    return 'Failure', 404
