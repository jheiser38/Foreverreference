# This blueprint is generated to handle all routes related to verifying users.

from flask import Blueprint

auth = Blueprint('auth',__name__)

# This imports the auth.views functions, not the main ones
from . import views
