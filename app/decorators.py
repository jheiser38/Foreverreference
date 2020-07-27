from functools import wraps
from flask import abort, flash
from flask_login import current_user
from .models import Permission

# Here is my example from what I could find out.
# This function takes an arguement, but it is overall the wrapper
# called by @dec(whatever)
# Both of these are in the main.views file
# These must be imported into the view function or else they will not run
def dec(address):
    # The name of this is meaningless, but must be passed f as an arg
    def theThing(f):
        # This is what creates the wrapper
        @wraps(f)
        # This function name also doesn't matter, but pass in the args that are
        #   brought with it when the view function is called
        def cnn(*args,**kwargs):
            # This is where the magic actually happens
            if not current_user.email == address:
                # See the associataed errors.py file for handling this
                abort(403)
            # IF it works out, the view function will be run as normal
            return f(*args,**kwargs)
        # This return cycle is necessary to get you out of this nightmare
        return cnn
    return theThing

#
def otherdec(f):
    return dec('jheiser38@gmail.com')(f)


def permission_required(perm):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args,**kwargs):
            if not current_user.can(perm):
                abort(403)
            return f(*args,**kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return permission_required(Permission.ADMIN)(f)
