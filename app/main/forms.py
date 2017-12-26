from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from . import steem_tool


class PaymentForm(FlaskForm):
    # TODO set regular expression for name
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    email = StringField('Email', validators=[Email(), Length(1, 64)])
    confirmed_email = StringField('确认Email', validators=[Email(), EqualTo('confirmed_email', message='Email必须相同')])
    amount = StringField('金额', render_kw={'readonly': True}, default="$1.5")
    submit = SubmitField('付款')

    def validate_username(self, field):
        if steem_tool.get_account(field.data):
            raise ValidationError('%s 已被注册.' % field.data)


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)], render_kw={'readonly': True})
    email = StringField('Email', validators=[Email(), Length(1, 64)], render_kw={'readonly': True})
    password = StringField('密码', render_kw={'readonly': True})
    agree = SelectField('我知道CNsteem不会保存我的密码，我已牢记', choices=[('N', 'No'), ('Y', 'Yes'), ])
    submit = SubmitField('注册')

    def validate_agree(self, field):
        if field.data != 'Y':
            raise ValidationError('请牢记密码!')
