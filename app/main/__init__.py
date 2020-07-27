# Essentially this blueprint is required since there is not one script running
# the application.  Now it is stretched out over multiple directories, so here
# we are.

# This blueprint maps view functions to urls.

# imports the module
from flask import Blueprint

# Makes a blueprint object, first arg is the blueprints name,
# second arg is module it will be located in (the parent app).
main = Blueprint('main',__name__)

# from the parent directory, import these files
# These are where the view functions/error handlers exist.
# Importing these scripts must take place after instantiating main due to
# circular dependencies.
# When these files are imported here, the blueprint object is tied to them.
from . import views, errors

# HEre is how you put something into the app context to preclude having to
# state it in every render_template and template:

# Just get thew thing you need
from ..models import Permission

# For the main app, every template rendered with Permission will use the value
#   for the key in the below dictionary.
#   key = Permission
#   value = Permission class from models.py
# If a app.app_context_processor is overidden in another blueprint, whichever
#   blueprint is registered last in app.__init__.py will take over.
# They will not do seperate things, you must choose different variables.
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)

#from flask_login import current_user

#@main.app_context_processor
#def inject_current_user():
#    return dict(current_user = current_user)
