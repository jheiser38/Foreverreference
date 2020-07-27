# This is flasks http authorization class, which makes logging in for apis easy.
from . import api
from flask import g, jsonify
from ..models import User
from flask_httpauth import HTTPBasicAuth
from .errors import forbidden, unauthorized
auth = HTTPBasicAuth()


# This is used to verify a users email and password when using api calls.
# Since this is in the api blueprint, it is independent of the application
#   verification process.
# This will require a secure http so that all requests are encrypted in transit.
@auth.verify_password
def verify_password(email_or_token,password):
    if email_or_token == '':
        return False
    if password == "":
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True # This is adeed to help the view functions determine
                            # how the user verified themselves
        return g.current_user is not None #returns either True or False
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    g.token_used = False
    # This is a flask context variable named g
    g.current_user = user
    return user.verify_password(password)


def auth_error():
    return unauthorized('Invalid credentials')


@api.route('/tokens/', methods=['POST'])
def get_token():
    # The phrasing here prevents users from re-upping their token using their
    #   current token.
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token':g.current_user.generate_auth_token(expiration=3600),
        'expiration':3600})


# This will run before a request is sent to the api blueprint
# All this prevents is a user, who is logged in and not confirmed, cannot move on
# This should not run if the user is not logged in yet.
# The mechanism for requests is that this will run before an api call, and the
#   auth.verify_login will run since auth is the login manager for api
@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and \
            not g.current_user.confirmed:
        return forbidden('Unconfirmed account')
