from flask_wtf import Form
from wtforms import StringField, PasswordField, FileField
from wtforms.validators import DataRequired, EqualTo, Length


# Set your classes here.

class Peers(Form):
    peers = StringField(
        'Peers', validators=[DataRequired(), Length(min=6, max=256)]
    )

class DecryptFile(Form):
    signature = StringField(
        'Signature', validators=[DataRequired()]
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