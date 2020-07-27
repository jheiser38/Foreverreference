from . import api
from .. import db
from ..models import Comment, Post, Permission
from .decorators import permission_required
from flask import g, url_for, jsonify, request,current_app

# This will return all comments
@api.route('/comments/')
def get_comments():
    extra = request.args.get('extra',None)
    page = request.args.get('page',1,type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page,per_page=current_app.config['COMMENT_PER_PAGE'],error_out=False
        )
    comments = pagination.items
    prev = None
    if pagination.has_prev:
        prev = page - 1
    next = None
    if pagination.has_next:
        next = pagination + 1
    return jsonify({
        'comments':[comment.to_json() for comment in comments],
        'prev_url':prev,
        'next_url':next,
        'count':pagination.total,
        'extra':extra
        })

# this will return a specific comment
@api.route('/comments/<int:id>')
def get_comment(id):
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_json())

# This will return all comments for a specific post
@api.route('/posts/<int:id>/comments/')
def get_post_comments(id):
    post = Post.query.get_or_404(id)
    comments = post.comments
    return jsonify({
        'post':post.to_json(),
        'comments':[comment.to_json() for comment in comments]
        })

# This will return post a comment for a specific post
@api.route('/posts/<int:id>/comments/', methods=["POST"])
@permission_required(Permission.COMMENT)
def new_comment(id):
    post = Post.query.get_or_404(id)
    comment = Comment.from_json(request.json) # this returns a comment object
    comment.post = post
    comment.author = g.current_user
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_json()), 201, \
        {'Location':url_for('api.get_comment',id=comment.id)}
