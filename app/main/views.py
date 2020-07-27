from datetime import datetime
from flask import render_template # Renders the template provided using jinja2
    # return render_template(templateFolderFile, values to put in HTML files)
from flask import session       # session is a dictionary which stores values
    # for the context of the app
from flask import redirect      # Gives the browser a new url to navigate to
    # return redirect(URL)
from flask import url_for       # Provides the URL for a view function using the app.url_map
    # redirect(url_for('NAME',_external=True))
    #   This will return a url, external makes it a complete http://URL vice local
    # redirect(url_for('NAME',variable=value))
    #   This is how you do dynamic urls, i.e. for usernames
    #   Must have a <variable> in the app.route(URL)
from flask import request       # Allows using the request object
# from the parent directory (which includes its __init__ file), import the blueprint
from flask import current_app # allows you to use the methods/properties of the
                        # current app context
from flask import abort # allows for error handling
from . import main
# from the forms folder in the directory, import the form for use
from .forms import NameForm, EditProfileForm,EditProfileAdminForm, PostForm,\
        CommentForm
# from the parent's parent directory __init__ file, import the database
from .. import db
# from the models folder, import the User table, since thats what were using
from ..models import User, Permission, Role, Post, Comment
# Necessary for sending emails
from ..emails import send_email
# this is necessary to provide flash messages
from flask import flash
from flask import make_response # This allows you to construct a response object
                                # before it is returned.
# from flask_mail import Message, Mail
# from threading import Thread
from flask_login import current_user,login_required # allows for referencing the logged in user
from ..decorators import admin_required, permission_required,otherdec

# This is the main page where all the posts from all the users can be viewed.
@main.route('/', methods=['GET','POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit() and current_user.can(Permission.WRITE):
        p = Post(body=form.body.data, author=current_user._get_current_object())
            # The _get_current_object() is necessary because the current_user is
            # a proxy variable, and the _get_current_object will return the
            # actual object that is the user.
        db.session.add(p)
        db.session.commit()
        return redirect(url_for('.index'))
    # This will display all the posts to the site, not just for the specific user.
    # posts = Post.query.order_by(Post.timestamp.desc()).all()

    # This is how you only show a certain amount of posts in a page
    # This gets the page from the request, and returns a 1 if no page is given
    # If the arg cannot be converted into an integer, you also get 1.
    page = request.args.get('page',1,type=int)

    # Here is where it will either show all posts or just the followed posts.
    # This pulls a cookie from its dictionary in the request object for reference
    # There will be buttons which will set the cookie later.
    show_followed = False
    if current_user.is_authenticated:
        # bool('') will return False, bool('anything') will return True
        show_followed = bool(request.cookies.get('show_followed',''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query

    # This is an object of class Pagination, which is made from a query.
    # The query is then paginated (sqlalchemy default method).
    # This pagination takes the page number as the only required arguement.
    # The url request will look like ...5000/?page=2
    #   Pagination objects have attributes like has_next, next_num, which can be
    #       used to navigate through the pagination object.
    #   They also have methods on using the pagination widget, which will be
    #       covered later.
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config['POST_PER_PAGE'], # per_page default=20
        error_out=False) # error_out will send 404 if the page range is invalid
    # This will return the posts for the page provided to the pagination
    posts = pagination.items
    return render_template('index.html',form = form, posts = posts,
        pagination=pagination,show_followed = show_followed)
#
# This will be the profile page for users to view someones profile page.
@main.route('/user/<username>')
@login_required
def user(username):
    # The first_or_404 will send error code 404 if the query results in None.
    # This prevents the html form rendering with no data (i.e. user = None).
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page',1,type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config['POST_PER_PAGE'], # per_page default=20
        error_out=False)
    posts = pagination.items # Returns a list of items for the current page.
    return render_template('user.html',user=user,posts=posts, pagination=pagination)

# This function serves to allow users to change the simple things about their
#   profile (location, name, about_me).
@main.route('/edit_profile', methods = ['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user',username=current_user.username))
    # Since this view just replaces all data, form is pre-populated
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', form = form)


@main.route('/edit_profile/<int:id>', methods=["GET","POST"])
@login_required
@admin_required
def edit_profile_admin(id):
    # .get() will search the table by the primary key
    # This will return a 404 error if the user.id does not exist
    # The first() is not necessary since it will return a User object
    user = User.query.get_or_404(id)
    # Allthough this form does not take any arguements, one is passed in here to
    #   be assigned as the user in the
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.email = form.email.data
        # Again, this is necessary because the data stored is an int, not a Role
        user.role = Role.query.get(form.role.data)
        user.location = form.location.data
        user.name = form.name.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash(f"{user.username}'s profile has been updated.")
        return redirect(url_for('main.user',username = user.username))
    form.name.data = user.name
    form.username.data = user.username
    form.email.data = user.email
    form.location.data = user.location
    form.about_me.data = user.about_me
    # This is passed in this way because the form stores the field as an integer ,
    #   and will reverse lookup the value for the role to display the text
    form.role.data = user.role_id
    form.confirmed.data = user.confirmed
    return render_template('edit_profile.html',form = form, user = user)

# This function shows a post as its own link
@main.route('/post/<int:id>', methods=["GET","POST"])
@login_required
def post(id):
    form = CommentForm()
    post = Post.query.get_or_404(id)
    if form.validate_on_submit():
        c = Comment(body=form.body.data, post=post, author=current_user._get_current_object())
        db.session.add(c)
        db.session.commit()
        flash("Your comment has been posted.")
        return redirect(url_for('main.post',id=id, page=-1))
    page = request.args.get('page',1,type=int)
    # This will pull up the last page, which is where your comment will be.
    if page == -1:
        page = (post.comments.count() -1) //\
            current_app.config["COMMENT_PER_PAGE"] + 1 # + 1 is added to the end
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['COMMENT_PER_PAGE'],error_out=False)
    comments = pagination.items
    return render_template('post.html',posts=[post],form=form,
        comments=comments, pagination=pagination)

# This is here to edit the post's contents
@main.route('/edit_post/<int:id>', methods = ['GET','POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    if not current_user.id == post.author_id and not current_user.is_administrator():
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash("Post updated.")
        return redirect(url_for("main.index"))
    form.body.data = post.body
    return render_template('edit_post.html', form = form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid username.')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('You already follow this user.')
        return redirect(url_for('main.index'))
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {user.username}')
    return redirect(url_for('main.index'))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid username.')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash('You do not follow this user.')
        return redirect(url_for('main.index'))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You are no longer following {user.username}')
    return redirect(url_for('main.index'))

@main.route('/followers/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid username.')
        return redirect(url_for('main.index'))
    page = request.args.get('page',1)
    pagination = user.followers.paginate(
            page, per_page=current_app.config['FLASK_FOLLOWERS_PER_PAGE'],
            error_out=False)
    follows = [{'user': item.follower, 'timestamp':item.timestamp}
            for item in pagination.items]
    return render_template('followers.html',user=user,title='Followers of',
            endpoint='.followers',pagination=pagination,follows=follows)

@main.route('/following/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def following(username):
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('Invalid username.')
            return redirect(url_for('main.index'))
        page = request.args.get('page',1)
        pagination = user.followed.paginate(
                page, per_page=current_app.config['FLASK_FOLLOWERS_PER_PAGE'],
                error_out=False)
        follows = [{'user': item.followed, 'timestamp':item.timestamp}
                for item in pagination.items]
        return render_template('following.html',user=user,title='Followings of',
                endpoint='.following',pagination=pagination,follows=follows)


# This function explores the use of cookies, and how it uses them to determine
#   how the webpage is displayed to users.
@main.route('/all')
@login_required
def show_all():
    # This defines a request object, which is normally returned at the end of
    #   a view function.
    resp = make_response(redirect(url_for('.index')))
    # This sets a cookie in the request object
    #   set_cookie(cookieName,value,args**)
    # The max age will save the cookie for 30 days.
    resp.set_cookie('show_followed','',max_age=60*60*24*30)
    # and finally, return the request object to tell flask ro pull up the page.
    return resp


# This is an extension of the above function, just for actually setting the cookie.
@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed','1',max_age=60*60*24*30)
    return resp

# This view function is used to show all the comments, and they can be deleted or
#   enabled if the user is a moderator.
@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page',1,type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page,per_page=current_app.config['COMMENT_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('moderate.html',comments=comments,
        pagination=pagination,page=page)

# This just updates the db to enable the comment.
@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    flash(f"Comment has been enabled: {comment.body}")
    return redirect(url_for('main.moderate',
        page=request.args.get('page',1,type=int))) #returns you to where you were.

# This just updates the db to disable the comment.
@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    flash(f"Comment has been disabled: {comment.body}")
    return redirect(url_for('.moderate',
        page=request.args.get('page',1,type=int)))


# This route exists to shutdown the application manually
@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing: # This is automatically populated if app in test
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown() # This is a function werkzeug puts in the environment
    return "Shutting down..."


from flask_sqlalchemy import get_debug_queries
# This function takes the queries issued during a request as a list which contains
#   times, SQL statement, and more information about the query starting point.
# If the query takes longer than the allowed time, it is logged into the flasks
#   logger file, which is created in the config.py
# At the end, the response is returned as normal.
@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                    f'Slow query: {query.statement}\n\
                    Parameters:{query.parameters}\n\
                    Duration:{query.duration}\n\
                    Context:{query.context}')
                    # SQL statement
                    # parameters input
                    # Amount of time it took
                    # file calling the query

    return response

################################################################################
################################################################################
#### The apps beyond this point demonstrate specific things for flask apps #####
################################################################################
################################################################################


# This app is in here since it was the first one, pretty useless now.
# main is used instead of app because it is tying this view function to the
# blueprint, so it can be given to the app.
@main.route('/old_index', methods=['GET', 'POST'])  # See changed route
def old_index():
    """
        This functions serves as the main page for this application.
    """

    # This sets the NameForm as the form to render the template below
    form = NameForm()

    # instead of having a "if METHOD == POST", this iformat is used with FlaskForm
    if form.validate_on_submit():
        # See models.py for more information on using SQLAlchemy
        user = User.query.filter_by(username=form.name.data).first()
        # used to create a new user if a None object is returned
        # Now its here as a reference
        if user is None:
            flash(f'We see that you are new.\nWelcome {form.name.data}!')
            # user = User(username=form.name.data)
            #db.session.add(user)
            #db.session.commit()
            #session['known'] = False # previously used to render html
            #if app.config['FLASKY_ADMIN']:
                #send_email('jheiser38@gmail.com', 'New User',
                     #  'mail/new_user', user=user)
        else:
            # just a session variable for rendering the HTML (see the template)
            flash(f'Welcome back {user.username}')
            # Here is defining a session variable.
            #session['known'] = True
        #session['name'] = form.name.data

        # This redirects to itself, i.e. reloads the page.
        # IT is good practice to end a POST with redirect so that refreshing
        # doesn't cause data to be resubmitted, and then you have a fucked up db.
        # Redirect using .index vice index will apply the current blueprint to get
        # main.index, which is the desired method to get the view function.
        # This supports use of multiple blueprints.

        return redirect(url_for('.old_index'))  # see changed url based on blueprint
                                            # can also be main.index if in a different
                                            # Blueprint

    # if essentially the method is GET, grab the sessions variables and load it
    return render_template('old_index.html', form=form)

# This app demonstrates using url arguments
# NOTE: url does not need <> around the text when you run it, only used in the script
# Can use string, int, float, or path as qualifiers
# You can also setup multiple urls based on if it meets the qualifiers
#   e.g. string vice int for different things
# This also includes a redirect example.
@main.route('/testMe/<int:num>/<message>', methods=['GET'])
def testdynamic(num,message):
    if num == 69:
        return f'<h1>Here\'s the number: {num} and the message: {message}'
    return redirect(url_for('.testdynamic',num=69,message='heyYou'))

# This is another example of using dynamic urls and the redirection
@main.route('/test_moment')
def test_moment():
    return render_template('test_moment.html',current_time=datetime.utcnow())

@main.route('/testmsg')
def testmsg():
    send_email(
        'jheiser38@gmail.com',
        'Subject',
        'mail/test',
        testVal='TestMeME')
    return redirect(url_for('.index'))

# Here is use of custom decorators
# See app.decorators for more info
# Always put the route decorator first, then put the rest in the order you would
#   like to run them at (logged_in -> admin_required)
@main.route('/admin_required')
@admin_required
def permission1():
    return 'Congrats, your an admin'

@main.route('/permission_required')
@permission_required(Permission.FOLLOW)
def permission2():
    return render_template('mail/test.html')

@main.route('/email1')
@otherdec
def permission3():
    return "congrats, you got a gud email."
