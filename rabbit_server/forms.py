import os
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, SubmitField
from wtforms.validators import Required, Length


WTF_CSRF_SECRET_KEY = os.urandom(24)


class LoginForm(Form):
    name = TextField("name", validators=[
        Required(message='Username'),
        Length(min=1, max=100, message='1-100')
    ])
    password = PasswordField('password', validators=[
        Required(message='Password'),
        Length(min=1, max=100, message='1-100')
    ])
    submit = SubmitField('login')
