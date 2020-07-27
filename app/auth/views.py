from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, request
from . import auth # Imports the valid blueprint
# imports all the forms used in the view functions
from .forms import LoginForm, RegistrationForm,ResendEmailForm,ChangeEmailForm,\
    ForgotPasswordForm,ResetPasswordForm,ChangePasswordForm
from .. import db
from ..models import User
from flask_login import login_required # this is used to state login is required
                                       # to view a page, used as a decorator
# This grabs the current app context, which is really used for sending emails
# and grabbing the app.config values
from flask import current_app
from ..emails import send_email
from flask_login import login_user # This is used to login the user
from flask_login import logout_user # This is used to logout the user
from flask_login import current_user # Allows for referencing the current user
                    # The current_user is the row of data from the user table
                    # for the currently logged in user (see models.py)
# This is required to create encrypted tokens (used for sending emails)
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


# Due to the blueprint configuration, the /auth needs to be before the route below
@auth.route('/login', methods=['GET','POST'])
def login():
    """
        This view function serves as a means to verify users credentials.
    """
    # Redirects if they are already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        # Note: all emails in this db are lowercase, so user input must be converted
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            # The user will not be allowed to access any pages past the auth
            # due to the handler below (auth.before_app_request)

            # This writes the ID of the user (as a sring) to the current session.
            # the 2nd arguement will set a long term cookie in the users browser.
            login_user(user,form.remember_me.data)

            # If you try to get to a secret page, you will be redirected to
            # the login, and the page you were trying to access is in the url
            # courtesy of flask-login.  This next business will send you to your
            # target location if you had one, or home if you are just logging in.
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        else:
            flash('Invalid username or password.')
    return render_template('auth/login.html',form=form)

# When using multiple decorators, the decorator applies to the route below it.
# Here is how you would implement that authentication is required to view a function
@auth.route('/secret')

# This right here is what does it, this is the decorator used by flask_login
# Once the user is authorized, flask registers the route
# If the user is not logged in, flask_login will return them to the login page
#   and will flash('Please log in to access this page.')
# This default login page is configured in app.__init__.py
@login_required
def secret():
    return 'Only authenticated users allowed here'

# This is used to essentially clear the current_user value
@auth.route('/logout')
@login_required
def logout():
    logout_user() # Deletes the user ID from the session
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

# This is used to register a new user
# The data is gathered, db populated, and a confirmation email sent out.
@auth.route('/register',methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
            email=form.email.data.lower(),
            password=form.password.data, # See models.py for handling passwords
            role_id=None)
        db.session.add(user)
        db.session.commit()
        # The user is needed to be committed to get a user.id, and also to
        # reference it later rather than getting information twice.
        user = User.query.filter_by(username=form.username.data).first()
        # This is a method of the User class, and returns an encrypted dictionary
        # with the users id.
        token = user.generate_confirmation_token()
        send_email(
            user.email,
            'Confirm Email',
            'auth/mail/confirm_user',
            user=user,
            token=token
            )
        flash("A confirmation request has been sent to your email!")
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html',form=form)

# This takes the token sent to confirm the email, and decrypts it to update the db
# I do this outside of a models.py method because I dont know the user is logged in
@auth.route('/confirm/<token>')
def confirm(token):
    # This is the Serializer object
    # This is used to encode and decode messages
    # Messages have time stamps, which are encoded with the message
    # Note: the encrypted messages are in bits, and to be used in urls, must be
    #   decoded into utf-8, and then encoded to decrypt them on the other side.
    # in this instance, it is decrypting a token sent via url.
    # the token has a python dictionary in it (see models.py)
    s = Serializer(
        current_app._get_current_object().config['SECRET_KEY'],
        expires_in=60)
    # If invalid code or expired, will return an error.
    try:
        data = s.loads(token.encode('utf-8'))
    except:
        flash('Invalid or expired confirmation token.')
        return redirect(url_for('.login'))
    # gets the user in the database if the ID exists, and confirms the email.
    user = User.query.filter_by(id=data['confirm']).first()
    if user.confirmed is False:
        user.confirmed = True
        db.session.add(user)
        db.session.commit()
        flash('User email confirmed.')
    else:
        flash("Email already confirmed.")
    return redirect(url_for('.login'))

# This will automatically show courtesy of the auth.before_app_request handler
# if the request is made with a user logged in to an unconfirmed profile
@auth.route('/unconfirmed',methods=['GET','POST'])
def unconfirmed():
    # This doesn't allow users who aren't logged in, or previously confirmed
    # to view the page.
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    # There's probably a better way to do this, but I am lazy.
    # The author writes another route for resending things, whereas I display
    #   the unconfirmed page and handle resending in one view function.
    # This just allows for them to resend the confirmation email
    form = ResendEmailForm()
    if form.validate_on_submit():
        token = current_user.generate_confirmation_token() # method of the User
        send_email(
            current_user.email,
            'Confirm Email',
            'auth/mail/confirm_user',
            user=current_user,
            token=token
            )
        flash("A confirmation request has been sent to your email!")
        return redirect(url_for('.login'))
    return render_template('auth/unconfirmed.html',form=form)


# This is just simply a profile page which shows your profiles data.
@auth.route('/change_info',methods=["GET","POST"])
@login_required
def change_info():
    return render_template('auth/change_info.html',user=current_user)


# Here is a page where you can change your email address.
# It will not change until you enter the confirmationcode
@auth.route('/change_email',methods=["GET","POST"])
@login_required
def change_email():
    form=ChangeEmailForm()
    if form.validate_on_submit():
        token = current_user.generate_email_token(form.new_email.data.lower()) # method of the User
        send_email(
            form.new_email.data.lower(),
            'Confirm Email',
            'auth/mail/confirm_email',
            user=current_user,
            token=token
            )
        flash("A confirmation request has been sent to your email!")
        return redirect(url_for('.login'))
    return render_template('auth/change_email.html',form=form,user=current_user)


# This is how you update your email
# The confirm_email function returns boolean,message
#   True means process the change
# The email is checked to not exist in the db prior to adding (see models.py)
@auth.route('/update_email/<token>')
@login_required
def update_email(token):
    input = current_user.confirm_email(token)
    if input[0]:
        flash(f'{input[1]}')
        db.session.commit()
        return redirect(url_for('.change_info'))
    else:
        flash(f'{input[1]}')
        return redirect(url_for('.change_info'))


# This is how you send an update password email
# The user will see the same thing if an email is or is not sent, for security
@auth.route('/forgot_password',methods=['GET','POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_confirmation_token()
            send_email(
                user.email,
                'Update Password',
                'auth/mail/reset_password',
                user=current_user,
                token=token
                )
        flash('Confirmation email sent.')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html',form=form)


# This is what will actually change your password if you provide a valid token
# Token is encrypted same as for confirming users
@auth.route('/reset_password/<token>',methods=['GET','POST'])
def reset_password(token):
    s = Serializer(
        current_app._get_current_object().config['SECRET_KEY'],
        expires_in=60)
    try:
        data = s.loads(token.encode('utf-8'))
    except:
        flash('Invalid or expired confirmation token.')
        return redirect(url_for('.login'))
    # I store a session variable here, which cannot be altered without this
    # function running in its entirety.  Also, there's no logged in user.
    session['temp_user_id'] = User.query.filter_by(id=data['confirm']).first().id
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=session.get('temp_user_id')).first()
        user.password = form.password.data
        db.session.add(user)
        db.session.commit()
        flash('Password reset.')
        return redirect(url_for('auth.login'))
    return render_template('auth/change_password.html',form=form)


# This page is used to volountarily change a password (not out of need to reset)
@auth.route('/change_password',methods=['GET','POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.crt_pword.data):
            current_user.password=form.new_pword.data
            db.session.add(current_user)
            db.session.commit()
            flash("Password has been updated.")
            return redirect(url_for('.change_info'))
        else:
            flash('Invalid password.')
    return render_template('auth/change_password_elective.html',form=form)

# This will prevent users who have not confirmed their email from accessing more.
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and \
            request.endpoint and \
            request.blueprint != 'auth' and \
            request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed')) # send them to resend the email
