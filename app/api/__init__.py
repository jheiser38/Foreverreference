from flask import Blueprint

api = Blueprint('api', __name__)

# Each different api call is a different file.d
from . import authentication, posts, users, comments, errors
