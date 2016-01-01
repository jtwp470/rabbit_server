import os
from flask.ext.wtf import Form, RecaptchaField
from wtforms import TextField, PasswordField, SubmitField
from wtforms.validators import Required, Length, Regexp, Email, EqualTo


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


class RegisterForm(Form):
    username = TextField("User name", validators=[
        Required(message="[a-zA-Z0-9]+"),
        Length(min=1, max=100),
        Regexp(r"[a-zA-Z0-9]+")
    ])
    email = TextField('Email Address', validators=[
        Required(),
        Email("Invalid email address.")
    ])
    password = PasswordField('Password', validators=[
        Required(),
        EqualTo('confirm'),
        Length(min=6, max=100,
               message="Your password is shoten. Need 6 characters.")
    ])
    confirm = PasswordField('Repeat Password')
    recaptcha = RecaptchaField()
