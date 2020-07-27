from ..models import User
from flask import jsonify, url_for
from . import api


# This will return a user page when given an id
@api.route('/users/<int:id>')
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())

# This will return all posts by a specific user.
@api.route('/users/<int:id>/posts/')
def get_user_posts(id):
    user = User.query.get_or_404(id)
    return jsonify({
        'user':url_for('api.get_user',id=id),
        'posts':[post.to_json() for post in user.posts]
    })


# This will return all the posts a user follows
@api.route('/users/<int:id>/timeline/')
def get_user_followed_posts(id):
    user = User.query.get_or_404(id)
    return jsonify({'posts':[post.to_json() for post in user.followed_posts]})
