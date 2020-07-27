from flask import jsonify, g, url_for, current_app, request
from .. import db
from .errors import forbidden
from . import api
from .decorators import permission_required
from ..models import Post, Permission


# This function uses the to_json method from the models.py for Post, and will
#   return a jsonified list of posts.
@api.route('/posts/')
def get_posts():
    page = request.args.get('page',1,type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config["POST_PER_PAGE"],error_out=False
    )
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts',page = page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts',page = page+1)
    return jsonify({
        'posts':[post.to_json() for post in posts],
        "prev_url":prev,
        'next_url':next,
        'count':pagination.total
        })

# This function will return a specific post when given an ID.
@api.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())

# This functions is used to create a post using the api.
# This takes a json request and uses the from_json method from models.py to
#   convert it into a post object.
@api.route('/posts/',methods=["POST"])
# This uses a modified version of the decorators.py used in the overall, but this
#   one is listed in the api folder.
# It uses this one, because that is what we import into this file.
@permission_required(Permission.WRITE)
def new_post():
    # This
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    # This is what is returned to the user.
    # The post text, 201 status code for posted, and a link to the post.
    return jsonify(post.to_json()),201,\
        {'Location':url_for('api.get_post',id=post.id)}


# This function will be used to modify (PUT) an existing post object.
# It verifies the user is the author/ADMIN, and then updates the body, or uses
#   the same body from before.
# The from_json method from models.py is not called, because this is not a POST,
#   it is a PUT.
@api.route('/posts/<int:id>', methods = ["PUT"])
@permission_required(Permission.WRITE)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and \
        not g.current_user.can(Permission.ADMIN):
        return forbidden("Insufficient permissions")
    # This will change the post body, or keep it the same if the request is bum.
    post.body = request.json.get('body',post.body)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()),204,\
        {'Location':url_for('api.get_post',id=post.id),
        'newBody':post.body}
