from flask_wtf import Form
from wtforms import StringField, PasswordField, FileField
from wtforms.validators import DataRequired, EqualTo, Length


# Set your classes here.

class Peers(Form):
    peers = StringField(
        'Peers', validators=[DataRequired(), Length(min=6, max=256)]
    )

class Transaction(Form):
    sender = StringField(
        'Sender', validators=[DataRequired(), Length(min=6, max=256)]
    )
    recipient = StringField(
        'Recipient', validators=[DataRequired(), Length(min=6, max=256)]
    )
    file = FileField(
        'File', validators=[DataRequired()]
    )

class RegisterForm(Form):
    name = StringField(
        'Username', validators=[DataRequired(), Length(min=6, max=25)]
    )
    email = StringField(
        'Email', validators=[DataRequired(), Length(min=6, max=40)]
    )
    password = PasswordField(
        'Password', validators=[DataRequired(), Length(min=6, max=40)]
    )
    confirm = PasswordField(
        'Repeat Password',
        [DataRequired(),
        EqualTo('password', message='Passwords must match')]
    )


class LoginForm(Form):
    name = StringField('Username', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])


class ForgotForm(Form):
    email = StringField(
        'Email', validators=[DataRequired(), Length(min=6, max=40)]
    )
