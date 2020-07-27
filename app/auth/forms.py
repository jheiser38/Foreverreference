from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email
from wtforms.validators import Regexp
from wtforms.validators import EqualTo
from wtforms import ValidationError
from ..models import User

# Used to prompt the user for a login email and password
class LoginForm(FlaskForm):
    # When multiple validators are used, it works left to right until wrong.
    # Also shows how to put in custom messages.
    email = StringField('Email:', validators=[DataRequired(),
        Email(message='Thats not fkin right'),Length(1,64)])
    password = PasswordField('Password:',validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Submit')

# Form to register new users

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[DataRequired(),Email(),Length(1,64)])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$',  # start with letter, only letters/nums/or _ or .
               0, # This is the regexp flag, (no idea what that means rt now)
               'Usernames must have start with a letter, and only ' # message when fail
               'contain letters, numbers, dots or underscores.')])
    password = PasswordField('Password:',validators=[DataRequired()])
    # The EqualTo('fieldname',message=message if fail)
    # Note: field must be written as a string
    password2 = PasswordField('ReenterPassword:',validators=[
        DataRequired(),EqualTo('password',message='Passwords must match.')])
    submit = SubmitField('Register')

    # When a form has a method which starts with validate_fieldname, it will run
    # like other validators defined above for the subject field.
    def validate_email(self,field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username not available.')

# This is just my easy way to run a POST method (1 button, nicely formatted)
# The user must login in order to send the confirm email, but how else would
#   they know they need to confirm it except when logging in.
class ResendEmailForm(FlaskForm):
        submit = SubmitField('Resend confirmation email')

# Form used to change someones email
# Is converted to lower in the view function before the token is encrypted
# The users current email is rendered in the html
class ChangeEmailForm(FlaskForm):
    new_email = StringField('New Email:', validators=[DataRequired(),Email(),Length(1,64)])
    submit = SubmitField("Send confirmation code")

    def validate_new_email(self,field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')

# Form used to send a reset password email.
# If no email exists, no email is sent, but it is reported to the user as if it did.
# Email is turned to lower case in view function to match the database
class ForgotPasswordForm(FlaskForm):
    email = StringField('Registered Email:', validators=[DataRequired(),Email(),Length(1,64)])
    submit = SubmitField("Send confirmation code")

# Form used to reset a users password if forgotten
class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password:',validators=[DataRequired()])
    password2 = PasswordField('ReenterPassword:',validators=[
        DataRequired(),EqualTo('password',message='Passwords must match.')])
    submit = SubmitField('Update password')

# Form used to electively change your password.
class ChangePasswordForm(FlaskForm):
    crt_pword = PasswordField("Current Password:",validators=[DataRequired()])
    new_pword = PasswordField("New Password:",validators=[DataRequired()])
    new_pword2 = PasswordField("Reenter New Password:",validators=[DataRequired(),
        EqualTo('new_pword',message="Passwords must match.")])
    submit = SubmitField('Change password')



# SelectField is (data value, what they see)
# param = SelectField('What do you want to change?', choices=[('cpp', 'C++'), ('py', 'Python'), ('text', 'Plain Text')])
