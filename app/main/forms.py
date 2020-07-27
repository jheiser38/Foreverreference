# This is the file which contains all the forms used in this app.

from flask_wtf import FlaskForm # This is the module used for easy form creation

from wtforms import StringField, SubmitField, TextAreaField, BooleanField,\
                    SelectField# Select the form templates you want

# validators which are used to validate the form upon submit
from wtforms.validators import DataRequired,Length,EqualTo,Regexp,Email # Select the list of validators you want

from ..models import User, Role
from flask_pagedown.fields import PageDownField

# This form is used by users to change their own profile
class EditProfileForm(FlaskForm):
    name = StringField("Name:")
    location = StringField("Location:")
    about_me = TextAreaField("Tell us about yourself:")
    submit = SubmitField('Submit')

# This form is used by the admin to change users profile, greater permissions
class EditProfileAdminForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
            'Usernames must have start with a letter, and only '
            'contain letters, numbers, dots or underscores.')])
    confirmed = BooleanField('Confirmed')
    email = StringField('Email', validators=[DataRequired(),Email(),Length(1,64)])
    # This is a drop down option.
    # Choices must be presented as a list of tuples. where (input, display)
    # coerce=int tells it to store the data in the form as an int vice the default
    #   which is a string.
    # This id will be used to query the db later to assign the desired role.
    role = SelectField('Role',coerce=int)
    name = StringField("Name")
    location = StringField("Location")
    about_me = TextAreaField("About Me")
    submit = SubmitField("Submit")

    # This will run once the form is submitted, and will
    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        # This will return a list of all the roles in the db.
        self.role.choices = [(role.id,role.name)
            for role in Role.query.order_by(Role.name).all()] #order_by does a-z
        # This is later used in the validations for email and username, to
        #   permit reentering the same username.
        self.user = user

    def validate_email(self,field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username not available.')

class PostForm(FlaskForm):
    # This type of field (when paired with proper encoding), shows the marked
    #   up display that the text will have.  It previews this right below the
    #   field so you can immediately see how it looks.
    # Kind of clunky .
    # using #, ##, or ### at the beginning of a line determines text size.
    body = PageDownField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField('Submit')

# This form is used to collect user comments on posts
class CommentForm(FlaskForm):
    body = StringField("", validators=[DataRequired()])
    submit = SubmitField('Post')


# This form is no longer used
class NameForm(FlaskForm):
    # This is later referenced in the view function via form.name.data
    # the validators are a list of validators applied to the input to check it.
    name = StringField('What is your name?', validators=[DataRequired()])
    # this is the submit button used
    submit = SubmitField('Submit')
