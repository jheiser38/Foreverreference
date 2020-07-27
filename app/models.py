# This file is used to show the tables in the database.
# GENERAL NOTES ON DB USE:
#   -to create the database with the filename given, in the terminal:
#       flask shell # this opens the flask terminal with the db preloaded (due to
#                   shell context processor)
#       db.create_all() # this creates the file
#   # end of creating it
#
#   -If you want to add rows to a table, using the same shell:
#       newRole = Role(name='RoleName') # an ID will be assigned upon commit
#       newUser = User(username='User',role=newRole)
#       db.session.add(newRole) # similar to github
#       db.session.commit() # similar to github, autonumbering happens here
#   # end up creating
#
#   -To see relationships:
#       newUser.role.name # returns RoleName
#       newRole.users # returns a list of users with the subject role
#   # end of referencing
#
#   -to query a table:
#       Role.query.filter_by(name='searchName').all()
#       # This returns a list of role objects meeting the criteria
#       # The all() must be added in order to get a list of objects
#       # can just spam .filter_by criteria until you get what you want
#       Role.query.

# from the parent directory (app) import the database, which is in SQL alchemy.
from . import db

import hashlib # required for using gravatar avatars.
from datetime import datetime

# This is the module used to create the password hash
# Similar to encrypted stuff, but I did not write it
from werkzeug.security import generate_password_hash, check_password_hash

# This is the later used to create the User table to give it properties/methods.
from flask_login import UserMixin, AnonymousUserMixin

# This is required to confirm user emails
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, flash, url_for

# These are used for rendering rich text in the PostForm
from markdown import markdown
import bleach

#from .api.exceptions import ValidationError # Used below to write out custom
                                            # error codes.


# This class is placed here to be referenced later as an object.
# It is often imported into other view functions.
# This is used to construct the role.permissions, see below for discussion
class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16

# Each table is generated from a class object, highlighted below.
class Role(db.Model):
    __tablename__ = 'roles' # defines the table's name
                            #   This is the name which will be used in references

    # this is the general format for table columns:
    #   -first is db.parameterType (String, Integer, etc.)
    #   -next is qualifiers (primary_key, unique, nullable, etc)
    id = db.Column(db.Integer, primary_key=True) # new column id
    name = db.Column(db.String(64), unique=True) # new column name

    # Relationships work as follows:
    #   -one-many relationship, where role is the one (one role, many users)
    #   -the backreference allows you to pull up users with the role
    #       -User.role
    #   -the role_id below

    #   -To see all users with the role, pick a role object and do .users
    # Format db.relationship(class_name,backref=usually_this_tblName,loading)
    # Assigning the relationship from the one side requires referencing the python
    #   object, so it is in capital letters.
    # The backref will create another invisible column in the User table, which
    #   will store the object it is in a relationship with.
    # As far as the lazy goes:
    #   -This overall controls how the data from the query is loaded
    #   -dynamic will return a query object when you run Role.users
    #       -therefore, role = Role.query.first(), this has a query stored in
    #           role.users, so the query will be run anytime you want to get suers
    #   -select will return a list of objects when you run Role.users
    #       -therefore, role = Role.query.first(), this will run the query when
    #           you run role.users
    #       -This is different than dynamic, because dynamic does not run the
    #           query immediately, and also allows you to apply filters to the
    #           query before running it
    #   -joined will run the query for users when you define or query the user
    #       -in other words, role = Role.query.first(), role will be loaded with
    #           all the users who fit that role, whereas this would not be defined
    #           in the other two
    #   -subquery will do the same thing as a joined, but is different in how
    #       sqlalchemy does it
    #   -You want to use:
    #       -dynamic if you want to use filter_by
    #       -joined.subquery if you want to preload all the data associated once
    #           rather than continuously running the same query over and over
    users = db.relationship('User', backref='role',lazy='dynamic')

    # This is a quicker way to determine user permissions, the default role is
    # User, which is the vast majority of interactions handled by the app.
    # Index this makes it easier to query.
    default = db.Column(db.Boolean, default=False, index=True)

    # This is the permissions ID, which will be tied to the class below.
    # This is structured as follows:
    #   1-Follow
    #   2-Comment
    #   4-Write
    #   8-Moderate
    #   16-Admin
    # By using this structure, the permissions can be added and you will know
    # exactly what permissions a user has (permissions = 10, moderate/comment)
    # This prevents you from using a list/dictionary to define roles, which is
    # mroe efficient.
    permissions=db.Column(db.Integer)

    # This is used to set default values if nothing else is given, similar to
    # putting a default above, but this takes data after the fact and changes
    # what is in the table, so useful language.
    # This will run once you instantiate a role (r=Role()), not when add/commit.
    def __init__(self,**kwargs):
        # This line gets the values given to the row, and assigns them to this
        # object
        super(Role,self).__init__(**kwargs)
        # now that this instance has the values given, setss permission to the
        # desired default value
        if self.permissions is None:
            self.permissions = 0

    # This is a static method, which means it can be run without an instance of
    # the object (i.e. role.method).
    # This is run simply by Role.insert_roles() or by rolename.insert_roles()
    # No self arguement needed, because it is a static method to the class, not
    #   the instant
    @staticmethod
    # This function is used for a few things:
    #   -This keeps all the roles and permissions in one concise location
    #   -Anytime this function is run, it will clear and update all permissions
    #       to match the table, and add any new roles.
    #   -This captures adding new roles, and updating old ones
    #   -The only thing this doesn't handle is deleting roles
    def insert_roles():
        # Here is where the roles are kept, change them as you like.
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator':[Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                        Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
                        Permission.MODERATE, Permission.ADMIN]
        }
        default_role = 'User'
        # For each item in the dictionary above
        for r in roles:
            # Find its match in the database
            role = Role.query.filter_by(name=r).first()
            if role is None:
                # or create a new one if it doesnt exist
                role = Role(name=r)
            # Clear its permission value in the db (set to 0)
            role.reset_permissions()
            # Add the permissions from the dictionary above
            for perm in roles[r]:
                role.add_permission(perm)
            # Set the role's default value to True or False based on what is the
            #   current default user role.
            role.default = (role.name == default_role)
            # and then add the modified role to the session
            db.session.add(role)
        # and push the changes to the db.
        db.session.commit()

    # For the below functions, the function will be called by:
    #   role.function_name(Permission.WRITE) because the permissions are held in
    #   the class below.

    # Since permissions are added, this one is straight forward
    def add_permission(self,perm):
        if not self.has_permission(perm):
            self.permissions += perm

    # relatively the same for removing
    def remove_permission(self,perm):
        if self.has_permission(perm):
            self.permissions -= perm

    # Set it back to 0 for no permissions
    def reset_permissions(self):
        self.permissions = 0

    # This uss bitwise comparison to determine user permissions
    def has_permission(self,perm):
        # This it a bitwise comparison
        # it essentially takes the binary form of the number, and for each bit
        # it will return the same bit if it matches, and a 0 if it does not.
        # Since our permissions table is set up using powers of 2, and the way
        # that binary numbers are constructed, this can be used to determine
        # if the user has the target permission.
        # 1&3 will return 1, and 3&1 will return 1 (order does not matter)
        return self.permissions & perm == perm

    # This is not necessary, but gives a readable string for debugging/testing.
    def __repr__(self):
        return '<Role %r>' % self.name

# This has to be here because it is referenced in forming the User model.
# Below is how the follower followee relationship is accomplished.
# There are 2 one-to-many relationships in the User model which link it to this
#   table.
# This table also stores extra data that is more than the relationship (date).
class Follow(db.Model):
    __tablename__='follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
        primary_key=True)
    timestamp = db.Column(db.DateTime,default = datetime.utcnow)


# This class has the attributes of both a db.Model and a UserMixin
class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    # Setting index to True essentially tells sqlalchemy that this field will be
    # frequently searched, so it configures things so that queries are quicker.
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())

    # datetime.utcnow() is normally a function, but the db.Column accepts functions
    #   as values, and will invoke the function when required
    member_since = db.Column(db.DateTime(),default = datetime.utcnow)

    # This is updated later with the ping(self) function below
    last_seen = db.Column(db.DateTime(),default = datetime.utcnow)

    # Many half of the on-many relationship
    # Typical terminology is to use the primary key as the value
    # Tablename of the referenced table is used, and the parameter also
    # When assigning a role, use user.role = RoleObject
    #   -Once the instance is committed to the database, the backref will populate
    #       both the Role object and the User you are committing
    #   -the backref in the relationship acts as an invisible table thich will
    #       populate with the RoleObject
    # When using a ForeignKey, the tablename must be used, so it is in lowercase.
    # To see the role of a user, select the user and do .role (links w/ above)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    # One side of one-many relationship with posts
    posts = db.relationship('Post', backref='author',lazy='dynamic')

    comments = db.relationship('Comment',backref='author',lazy='dynamic')

    # This field represents if the user has confirmed their email or not
    # it is later used by auth.before_app_request, and does not let the user
    # go on if they havent confirmed their email.
    confirmed = db.Column(db.Boolean,default=False)

    # Here is where the hash string is stored.
    # The Werkzeug hash function is used for this.
    # It essentially take the contents of the password, and makes a random string.
    # When verifying, it uses the same has function, and compares the results.
    password_hash = db.Column(db.String(128))

    # This is defined to preculde needing to continuously determine the avatar
    #   hash for a user.
    avatar_hash=db.Column(db.String(32))

    # This is the implementation of a many-to-many relationship
    # This is accomplished by having 2 one-to-many relationships, and a table
    #   which connects the 2 (shown below).
    # This contains all the users that this user is following.
    followed = db.relationship('Follow',
                                foreign_keys = [Follow.follower_id],
                                backref=db.backref('follower',lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
                                    # Cascade handles how related objects are
                                    # effected by manipulating the parent.
                                    # When a user is deleted, all entries in this
                                    # table with that user will be deleted.
                                    # If not specified, the value in the table
                                    # would become null, which is wasting memory.
                                    # All must be specified as to not rewrite the
                                    # cascade options completely.

    # This contains all of the followers this user has.
    followers = db.relationship('Follow',
                                foreign_keys = [Follow.followed_id],
                                backref=db.backref('followed',lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')


    # This method will run once a user is instantiated
    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        # This function assigns the user.role as a Role (either Admin or default)
        if self.role is None:
            # This will allow only the admin email registered to be an admin
            if self.email == 'jheiser38@gmail.com':#current_app.config['APP_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()

        # This has a user follow themselves so that they can see their own posts
        #   when displaying followed posts.
        self.follow(self)

    # This just makes an easier implementation of the has_permission function
    # This also ensures the user has a defined role
    def can(self,perm):
        return self.role is not None and self.role.has_permission(perm)


    # This will return if the user has admin privaledges
    # This gets its own function because it is a common use
    def is_administrator(self):
        return self.role.has_permission(Permission.ADMIN)


    # This is used to grab the user's avatar from gravatar.com
    # The gravatar site stores avatars based on your email, so you can easily
    #   grab byour picture for something.
    # It is encoded using the hashlib function, and is a md5 hash
    # size - size, rating-pg, g, x whatever, default is one of several options

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon',rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return f'{url}/{hash}?s={size}&d={default}&r={rating}'

    # So how does this password thing work:
    #   -Once the User.password value is assigned, the @password.setter function
    #       is run, and the password_hash is populated.
    #   -The User.verify_password() function can be run after the fact to verify
    #       credentials.
    #   -The same password string can have a completely different hash, that is
    #       how the hash function is written.
    # See below for use of the property and .setter functions

    # This demonstrates how the property, and .setter work:
    # If in the shell, you enter User.testMe, the property function runs.
    # If you run User.testMe = 'x', the .setter function runs

    #    @property
    #    def testMe(self):
    #        print ('it worked')
    #
    #    @testMe.setter
    #    def testMe(self,value):
    #        self.username=value

    @property
    def password(self):
        # Password is never stored in the program, it is write only using this.
        # This prevents reading the password variable once it is defined.
        raise AttributeError('(chuckles) HA, password cannot be read, you FOOL.')

    # This function sets the password_hash
    @password.setter
    def password(self,password):
        # This function takes a plain-text password, and returns a password hash.
        # Normally take 4 arguements, last two default values are best for most.
        # This is configured using werkzeug, and I have no idea what their
        #   hash is.
        self.password_hash=generate_password_hash(password)

    # This function verifies password input.
    def verify_password(self,password):
        # Takes a password hash and compares it to the password entered by the user.
        # Returns True if a match.
        return check_password_hash(self.password_hash,password)

    # Verifying users:
    # Overall process:
    #   -User creates an account, registers an email
    #   -That user is entered into the database
    #   -A token containing their user.id is encrypted with the secret_key as the
    #       cypher, and sent to their email.
    #       -the link sent to the email has the token as a dynamic url, so hitting
    #           the link will send then to an auth route with the token, which
    #           will then be decoded and confirm the user
    #   -When the link is selected, the token sent in the dynamic url is decoded
    #       and the user.id who was listed in the token is updated in the db as
    #       a confirmed user, and they can now access all the sites pages.

    # This will generate a confirmation token which will be used to verify the
    # users email.  utf-8 is required since transporting this via url, and the
    # encrypted token is represented in bits (b'token') (i.e. no bits in urls).
    def generate_confirmation_token(self,expires_in=60):
        # This is itsdangerous's TimedJSONWebSignatureSerializer. which takes 2
        # args: 1-the encryption key that everything will be encrypted with, and
        #   2-the time the token will expire.
        # When the token is decrypted, if it is past the time stamp, it will error
        # expires_in is here so you can change the number if you want to
        s = Serializer(current_app.config['SECRET_KEY'],expires_in)
        # This is how you get a encrypted message, normally represented in bits.
        #   s.dumps(message) where message can be written in python (dict below)
        # This is necessary as stated above (putting the token as a dynamic url)
        return s.dumps({'confirm':self.id}).decode('utf-8')

    # This is similar to that above, except it is used to update a users email.
    # Once the link is clicked, the id decrypted will be compared to the
    #   current user, and if they are the same, the email will update.
    def generate_email_token(self, email,expires_in=60):
        s = Serializer(current_app.config['SECRET_KEY'],expires_in)
        return s.dumps({'email':email,'id':self.id}).decode('utf-8')

    # This is how an encrypted token is used to run some code.
    # The same serializer is first defined using the same parameters.
    # The token is then decoded, compared to the current users id to ensure the
    #   correct profile is updated.
    # If they are a match, the email is updated, or reported as updated.
    # This function returns a boolean, and a message which will be shown to the
    #   user based on how this confirmation goes.
    def confirm_email(self,token):
        s = Serializer(current_app.config['SECRET_KEY'])
        # If this fails, it is because the token is bad or has expired.
        try:
            data=s.loads(token.encode('utf-8'))
        except:
            return False,'Code invalid or expired.'
        # This ensures that no duplicate email addresses exist in the db.
        # This accounts for some lapse in time between email update and confirm
        if User.query.filter_by(email=data['email']).first():
            return False,"Email address is no longer available"
        # Ensures the current user is logged in to update their email.
        # This function also requires login in the view function.
        # See the message printouts for the meaning of each result.
        if self.id == data['id']:
            if self.email == data['email']:
                return False,'Email already confirmed.'
            self.email=data['email']
            self.avatar_hash = self.gravatar_hash()
            db.session.add(self)
            return True,'Email has been updated.'
        else:
            return False,'You must be logged in to update your email.'

# Below is STUPID, verify emails before allowing them to sign in.
    # This takes the token, decodes the utf-8, and then unencrypts it to see if
    # the contents match the user id.
    # This id will be checked against the user who is currently logged in.
        # I dont ageree with this method, because I would rather it just check
        # the number first, and uninvolve the logged in user aspect.
#    def confirm(self,token):
#        s = Serializer(current_app.config['SECRET_KEY'])
#        try:
#            data = s.loads(token.encode('utf-8'))
#        except:
#            return False
#        if data.get('confirm') != self.id:
#            return False
#        self.confirmed = True
#        db.session.add(self)
#        return True

    # This function is called by the before_app_request function
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    # This part will define actions regarding followers:

    # This will add a follow row when a user follows another user.
    # This creates a new follow entry and uses the terminology of the relationship
    #   to define the follower and the followed.
    def follow(self,user):
        if not self.is_following(user):
            f = Follow(follower=self,followed=user)
            db.session.add(f)

    # This will delete the follow when a user wishes to unfollow another user
    # This searches the self's list of followed users, and then will return a
    #   follow row from the table if it is true.
    # If it does exist, the user is unfollowed.
    def unfollow(self,user):
        f = self.followed.filter_by(followed_id=user.id).first()
            # This must be searched because of the lazy='dynamic' int he followed
        if f:
            db.session.delete(f)

    # This searches a users list of followed and will return the logic response.
    def is_following(self,user):
        if user.id is None:
            return False
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    # This will return if the user is being followed by another user.
    # This does the same thing as above, but for followers.
    # Note: the terminology followers/followed comes from the relationship
    #   defined in the User model.
    def is_followed(self,user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    # This is an example of a database join.
    # This wil be used to get all the posts by users who are followed by this user.
    # It follows the following rules:
    #   -First query the table which you want the values for, Post in this case
    #   -Join the queried table with the other table which has additional
    #       search criteria, Follow in this case.
    #   -Grab the initial data from Post by selecting criteria from the linked
    #       Follow table, linking ids in this case.
    #   -Filter those results (not filter_by) by applying one more criteria to
    #       either field.
    #   -This will return a query object.
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

    # This is a static method, which can be run from the shell.
    # This is like a late patch to add follows for all users.
    # This is done late, because the follows table was added after we had
    #   created all the users.
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    # This below is used to provide access tokens for api clients
    # This allows them to verify their credentials without having to log in
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id':self.id}).decode('utf-8')

    # This will take in a token, and either return a user or None
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token) #.encode('utf-8')?
        except:
            return None
        return User.query.get(data['id'])

    # This is what will be provided when the api calls for a user
    # This does not include email and role for privacy reasons
    def to_json(self):
        json_user = {
            'url':url_for('api.get_user', id=self.id),
            'username':self.username,
            'member_since':self.member_since,
            'last_seen':self.last_seen,
            'posts_url':url_for('api.get_user_posts',id=self.id),
            'followed_posts':url_for('api.get_user_followed_posts',id=self.id),
            'post_count':self.posts.count()
        }
        return json_user

    def __repr__(self):
        return '<User %r>' % self.username

class Post(db.Model):
    __tablename__='posts'
    id = db.Column(db.Integer,primary_key=True)
    # db.Text has no limitation on length
    # This db field stores the raw markdown data for the column
    #   -see main.forms for more info
    # This will allow the post to be editted
    body = db.Column(db.Text)
    # This will take the input from the raw markdown data and create html text
    #   which will then be rendered by the website.
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True, default=datetime.utcnow())
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment',backref='post',lazy='dynamic')

    # This function is goin got take a body field and convert it to html using
    #   a set of allowed tags.
    # The field which gathers this is a PagedownField
    # So what happens is:
    #   -the target is the post object where the body is being set
    #   -the value is the body (which is what iss being listened to below)
    #   -oldvalue and initiator mean nothing right now
    #   -The body is converted to markdown text
    #   -That markdown text is scrubbed of any unapproved html tags
    #   -<a> links are written if hey put in messy hyperlinks (linkify)
    # Doing things this wya mitigates your risk to hakers using discrete html
    #   tags to hack your application
    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags = ['a','abbr','acronym','b','blockquote','code','em','i',
                'li','ol','pre','strong','ul','h1','h2','h3','p']
        target.body_html = bleach.linkify(bleach.clean(
                markdown(value,output_format='html'),
                tags=allowed_tags,strip=True
                ))

    # This function will serialize json information is stored for the post
    def to_json(self):
        json_post = {
            'url':url_for('api.get_post',id=self.id),
            'body':self.body,
            'body_html':self.body_html,
            'timestamp':self.timestamp,
            'author_url':url_for('api.get_user',id=self.author_id),
            'comments_url':url_for('api.get_post_comments',id=self.id),
            'comment_count':self.comments.count()
        }
        return json_post

    # This function below will be used to deserialize a json POST, vice serialization
    #   which is what the above is.
    # This will be called in api.posts
    # What is given to this function as an arguement is request.json, from there
    #   it is used to .get('body'), which will hopefully return some data.
    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            # This error is handled by api.errors.py with the @api.errorhandler
            #raise ValidationError("Post does not have a body.")
            pass
        return Post(body=body)



# This will listen to any time a body value is set (set to a new value), and will
#   run the associated script.
db.event.listen(Post.body,'set',Post.on_changed_body)


# This will define the comment table.
# Comments will have one to many relationships with Post and User
class Comment(db.Model):
    __tablename__='comments'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index = True, default = datetime.utcnow())
    disabled = db.Column(db.Boolean) # Will be used to remove offensive comments
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer,db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags = ['a','abbr','acronym','b','code','em','i',
                'strong']
        target.body_html = bleach.linkify(bleach.clean(
                markdown(value,output_format='html'),
                tags=allowed_tags,strip=True
                ))

    def to_json(self):
        json_comment = {
            'url':url_for('api.get_comment',id=self.id),
            'body':self.body,
            'body_html':self.body_html,
            'author_url':url_for('api.get_user',id=self.author_id),
            'timestamp':self.timestamp,
            'post_url':url_for('api.get_post',id=self.post_id)
        }
        return json_comment

    # This will create a comment object when given json
    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            #raise ValidationError("Comment does not have a body.")
            pass
        return Comment(body=body)

db.event.listen(Comment.body,'set',Comment.on_changed_body)

# This is placed here for the login_manager
# If the current user is anonymous, then the login manager will user these
#   functions to determine the user doesn't have any permissions
class AnonymousUser(AnonymousUserMixin):
    def can(self,perm):
        return False

    def is_administrator(self):
        return False



# This section designates a function to be invoked when the extension needs to
# load a user given a user_id.
from . import login_manager

# This decorator registers the function with flask-login, and will be called when
# it needs to retrieve info about the logged in user.
# This is called in the login view function, and provides the user object as a
# return at the time of login
# BUG: THIS DOES NOT ACCOUNT FOR UPDATES IN PERSONAL INFORMATION, but I dont use it yet.
@login_manager.user_loader
def load_user(user_id):
    # Thus user identifier passes as a string, so it must be converted to an int.
    # Returneed object will either be a User or None if the id is invalid
    return User.query.get(int(user_id))

# This tells the login manager to use the AnonymousUser class for the current_user
#   if the current user is anonymous
login_manager.anonymous_user = AnonymousUser



# This section below is to provide an example of a many-to-many relationship
# In this case the students can have multiple classes, and classes have multiple
#   students.
# The registrations is the table which connects the two to allow for many-many.
#registrations = db.Table('registrations',
#    db.Column('student_id',db.Integer,db.ForeignKey('student.id')),
#    db.Column('class_id',db.Integer,db.ForeignKey('class.id'))
#    )
#
#class Student(db.Model):
#    id = db.Column(db.Integer,primary_key=True)
#    name = db.Column(db.String)
#    classes = db.relationship('Class',
#        secondary=registrations,
#        backref=db.backref('students',lazy='dynamic'),
#        lazy='dynamic')

#class Class(db.Model):
#    id = db.Column(db.Integer,primary_key=True)
#    name=db.Column(db.String)
    #students = db.relationship('Student',secondary=registrations,
    #    backref=db.backref('classes',lazy='dynamic'),lazy='dynamic')
