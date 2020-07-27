import unittest
import re # regular expressions
from app import create_app, db
from app.models import User, Role

class FlaskClientTestCase(unittest.TestCase):

    # Again, like unittest tests, this will run at the beginning and teardown
    #   will run at the end.
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        # This is the test client, which will allow sending of requests.
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # This tests to see if the homepage exists, and if it runs correctly.
    def test_home_page(self):
        response = self.client.get('/',follow_redirects=True) # sends a GET request and gets a response
        self.assertEqual(response.status_code,200) #get the response back
        # Verifies text in the response, as_text is necessary since get.data
        #   returns bytes by default.
        self.assertTrue('New user?' in response.get_data(as_text=True))

    def test_register_and_login(self):
        # register a new account by passsing in data which would be submitted by
        #   the form usually.  Since csrf is disabled, you don't need to send
        #   a csrf with the form to validate it.
        response = self.client.post('/auth/register',data={
            'email':'john@example.com',
            'username':'John',
            'password':'cat',
            'password2':'cat'
        })
        self.assertEqual(response.status_code,302) #302 for posting

        # log in with the new account, using same data method
        response = self.client.post('/auth/login',data = {
            'email':'john@example.com',
            'password':'cat'
            },follow_redirects=True) # this means you will be redirected to unconfirmed
        self.assertEqual(response.status_code,200) #redirects mean you'll do a GET
        # be careful when looking for jinja2 text, it may be formatted weird
        self.assertTrue('You have not confirmed' in response.get_data(as_text=True))

        # send confirmation token
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token() # could use the url for it, but don't
        response = self.client.get(f'/auth/confirm/{token}',follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertTrue('User email confirmed.' in response.get_data(as_text=True))

        # logout
        response = self.client.get('/auth/logout',follow_redirects=True)
        self.assertEqual(response.status_code,200)
        self.assertTrue('You have been logged out.' in response.get_data(as_text=True))
