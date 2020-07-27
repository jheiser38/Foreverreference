import unittest
import time # Used to validate tokens expire
from app import create_app, db
from app.models import User, Role, Permission, AnonymousUser, Follow

# This testing module tests the user model, mainly password items.
# Run in terminal via flask test.


class UserModelTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # This test verifies the password is only set by the password setter.
    def test_password_setter(self):
        u = User()
        self.assertTrue(u.password_hash is None)
        u.password = 'x'
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='x')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u=User(password='x')
        self.assertTrue(u.verify_password('x'))
        self.assertFalse(u.verify_password('nope'))

    def test_unique_hash(self):
        u=User(password='x')
        u2=User(password='x')
        self.assertFalse(u.password_hash == u2.password_hash)

    def test_confirm_tokens(self):
        u = User(password='x',email='confm_tok1@example.com')
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_token(email='confm_tok2@example.com')
        self.assertTrue(u.confirm_email(token)[0])

    def test_expired_tokens(self):
        u = User(password='x',email='expir_tok1@example.com')
        u2 = User(password='x',email='expir_tok2@example.com')
        db.session.add(u,u2)
        db.session.commit()
        token = u.generate_email_token(email=u.email,expires_in=1)
        time.sleep(2)
        self.assertFalse(u.confirm_email(token)[0])

    def test_invalid_tokens(self):
        u = User(password='x',email='inval_tok1@example.com')
        u2 = User(password='x',email='inval_tok2@example.com')
        db.session.add(u,u2)
        db.session.commit()
        token = u.generate_email_token(email=u.email,expires_in=1)
        self.assertFalse(u2.confirm_email(token)[0])

    def test_default_role(self):
        u = User()
        self.assertTrue(u.role == Role.query.filter_by(default=True).first())

    def test_user_permissions(self):
        u = User(role=Role.query.filter_by(name='User').first())
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_moderator_permissions(self):
        u = User(role=Role.query.filter_by(name='Moderator').first())
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_admin_permissions(self):
        u = User(role=Role.query.filter_by(name='Administrator').first())
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertTrue(u.can(Permission.ADMIN))

    def test_anonymous_permissions(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_follow(self):
        user1 = User(username='User1')
        user2 = User(username='User2')
        db.session.add(user1,user2)
        db.session.commit()
        self.assertFalse(user1.is_following(user2))
        self.assertFalse(user2.is_followed(user1))
        user1.follow(user2)
        self.assertTrue(user1.is_following(user2))
        self.assertTrue(user2.is_followed(user1))
        user1.unfollow(user2)
        self.assertFalse(user1.is_following(user2))
        self.assertFalse(user2.is_followed(user1))

    # There are a lot of tests in his example that I cannot do since I did not
    # confirm tokens using db.User methods.
