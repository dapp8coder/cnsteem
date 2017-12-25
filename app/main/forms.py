from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from . import steem_tool


class RegisterForm(FlaskForm):
    # TODO set regular expression for name
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    email = StringField('Email', validators=[Email(), Length(1, 64)], default='test@gmail.com')
    # confirmed_email = StringField('确认Email', validators=[Email(), EqualTo('confirmed_email', message='Email必须相同')])
    password = StringField('密码', render_kw={'readonly': True})
    submit = SubmitField('提交')

    def validate_username(self, field):
        if steem_tool.get_account(field.data):
            raise ValidationError('%s already in use.' % field.data)
