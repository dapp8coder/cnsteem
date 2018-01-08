from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from . import steem_tool


class PaymentForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired('必填项'), Length(3, 15,'长度必须在3和16之间'),
                                              Regexp('^[a-z][a-z0-9.-]*[a-z0-9]$', 0,
                                                     '用户名必须由小写字母，0-9，破折号或点号构成，首字符必须为字母，必须以字母或数字结尾')])
    email = StringField('Email', validators=[Email('Email不合法'), Length(1, 64, '长度必须在1和64之间')])
    confirmed_email = StringField('确认Email',
                                  validators=[Email('Email不合法'), EqualTo('confirmed_email', message='Email必须相同')])
    amount = StringField('金额', render_kw={'readonly': True}, default="$2.00")
    submit = SubmitField('支付宝付款')

    def validate_username(self, field):
        name = field.data
        if name.count('.') >=2:
            raise ValidationError('用户名最多有一个点号')
        for n in name.split('.'):
            if len(n) < 3:
                raise ValidationError('以点号隔开的每一个分段长度要大于2')
        if steem_tool.get_account(name):
            raise ValidationError('%s 已被注册.' % field.data)


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)], render_kw={'readonly': True})
    email = StringField('Email', validators=[Email(), Length(1, 64)], render_kw={'readonly': True})
    password = StringField('密码', render_kw={'readonly': True})
    agree = SelectField('我知道CNsteem不会保存，并且无法帮我找回密码，我已牢记', choices=[('N', 'No'), ('Y', 'Yes'), ])
    submit = SubmitField('注册')

    def validate_agree(self, field):
        if field.data != 'Y':
            raise ValidationError('请牢记密码!')



class DelegateForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    steem_power = StringField('申请数量', render_kw={'readonly': True}, default='2 Steem Power')
    submit = SubmitField('申请')
