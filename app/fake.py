from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User, Post

# This function will generate 100 fake users using the faker module
# from the flask shell,  from app import fake and do fake.users() then fake.posts()
def users(count=100):
    fake=Faker()
    i = 0
    while i < count:
        u = User(
            email = fake.email(),
            username = fake.user_name(),
            password = 'password',
            confirmed = True,
            name = fake.name(),
            location = fake.city(),
            about_me = fake.text(),
            member_since = fake.past_date()
            )
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        # This will be raised if there is a field generated with duplicate values
        # and the field has the unique=True tag in it.
        # This is normally caught in the form by validating the username and
        #   password, but needs it here since you're essentially working in the
        #   terminal.
        except IntegrityError:
            # This clears the db commit()
            db.session.rollback()

# This will generate 100 fake posts and publish them
def posts(count=100):
    fake = Faker()
    # This is how you determine the number of rows in a table.
    user_count = User.query.count()
    for i in range(count):
        # This will offset the query by the number (0 to the end) and then will
        #   star the query.  SO if you offset by 2, and grab the first, you have
        # grabbed the third row in the table.
        u = User.query.offset(randint(0,user_count -1)).first()
        p = Post(
            body = fake.text(),
            author = u,
            timestamp = fake.past_date()
            )
        db.session.add(p)
    db.session.commit()
