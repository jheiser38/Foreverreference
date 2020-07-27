# This file is ultimately used as the app factory, and creates the contexts of
# all resources.
from flask import Flask         # Kinda the whole app we're in
from flask import render_template # Renders the template provided using jinja2
    # return render_template(templateFolderFile, values to put in HTML files)
from flask_bootstrap import Bootstrap   # Used for stylesheets
    # Used by calling bootstrap = Bootstrap(app)
from flask_mail import Mail, Message  # Allows for sending emails, see mail below
from flask_moment import Moment # Used to get datetime for global user
from flask_sqlalchemy import SQLAlchemy  # Allows for use of the db module
from config import config  # the config dict will select the appropriate Config
                            # The Config object in this has a bunch of environment
                            # variables, so they are iobject ed once for accuracyobject  flask_login import LoginManager # This will manage the user
from flask_login import LoginManager
from flask_pagedown import PageDown # This is used to create rich text entries

# This is necessary to use bootstrap stylesheets
bootstrap = Bootstrap()
# This is the object which will send emails.
mail = Mail()
# This is ultimately used to show the local time for global users
moment = Moment()
# Assigns the db object which will then be used as the database
db = SQLAlchemy()
# This assigns the login manager and its associated view function
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # login view function location (blueprint.view)
# Anonymouse users will be redirected to the login view when viewing a protected page

pagedown = PageDown() # This will be used as a TextAreaField in the post form

# this function creates the app context, which is how it appears to a user
# This is known as the app factory.
def create_app(config_name):
    app = Flask(__name__) # creates context
    app.config.from_object(config[config_name]) # applies all object shit to config
    #config[config_name].init_app(app) # matters if you have a function defined

    # Initialize the objects since they are not tied to the context created.
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    # From the parent directory (app), sub directory main (including __init__), import
    #   the blueprint as the name below
    # This blueprint (stored in the main folder), will use the views folder for
    #   app.routes, and errors for app.errorhandler
    from .main import main as main_blueprint
    # This registers the blueprint (which has been instantiated and tied to the
    # view and error functions) to the app.
    app.register_blueprint(main_blueprint)

    # Different blueprint registered for different view functions.
    from .auth import auth as auth_blueprint
    # This means that all routes for auth will be localhost:5000/auth/viewFunct
    # This prevents conflicting view function routes
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # Here is where the api blueprint is imported
    # Note the url_prefix has a v1 in it, this is necessary because the api
    #   is primarily called by outside users, so changes to the api could
    #   fuck up their shit if you just cart blanche made changes.
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    # Attach routes and custom error pages here

    return app
