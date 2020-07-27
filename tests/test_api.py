import unittest
import re # regular expressions
from base64 import b64encode
import json
from flask import url_for
from app import create_app, db
from app.models import User, Role, Post, Comment

class APITestCase(unittest.TestCase):

    # Again, like unittest tests, this will run at the beginning of ever test
    #   and teardown will run at the end.
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

    # This is used to create a dictionary which will be used to create the
    #   request url for the api call.
    def get_api_headers(self,username,password):
        return {
            'Authorization':
                'Basic ' + b64encode(
                    (username + ":" + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
            }

    def add_user(self):
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com',role=r,password='cat',confirmed=True)
        db.session.add(u)
        db.session.commit()

    # This ensures that the api authorization function is working correctly.
    # It will also ensure the user is confirmed.
    def test_no_auth(self):
        # Tes no credentials
        response = self.client.get('/api/v1/comments/',
        content_type='application/json')
        self.assertEqual(response.status_code,401)

        # Add unconfirmed user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com',role=r,password='cat',confirmed=False)
        db.session.add(u)
        db.session.commit()

        response = self.client.get(
            '/api/v1/posts/',
            headers = self.get_api_headers('john@example.com','cat'))
        # When it comes to getting json, you can either get it directly from
        #   the response item you wrote if it is not jsonified like below, or
        #   you can load it in from a jsonified response as shown below.
        self.assertEqual(response.status_code,403)


    # This tests writing and getting posts
    def test_posts(self):
        # This adds a user
        self.add_user()

        # This will write a post as john
        # This also demonstrates the general format for get and post requests
        #   which is:
        #   -self.client.METHOD(
        #       url as a string,
        #       headers which is used to construct the url for the specific request,
        #       data for request as a dictionary)
        response = self.client.post(
            '/api/v1/posts/',
            headers = self.get_api_headers('john@example.com','cat'),
            # This takes a dictionary arguement, and will convert it to json
            #   so that the request url will be able to pass the data
            data = json.dumps({'body':'body of the blog post'}))
        self.assertEqual(response.status_code,201)
        url = response.headers.get('Location') # I set this up
        self.assertIsNotNone(url)

        # This will get all the posts
        response = self.client.get(
        '/api/v1/posts/',
        headers = self.get_api_headers('john@example.com','cat'))
        self.assertEqual(response.status_code,200)

        # This will get the new post, by searching by id
        response = self.client.get(
            url,
            headers = self.get_api_headers('john@example.com','cat'))
        self.assertEqual(response.status_code,200)
        # This will take the data and turn it into the json dictionary which we
        #   originally turned into json for the post using jsonify.
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'],url)
        self.assertEqual(json_response['body'],'body of the blog post')
        self.assertEqual(json_response['body_html'],
            '<p>body of the blog post</p>')

        # This will change the subject post
        response = self.client.put(
            url,
            headers = self.get_api_headers('john@example.com','cat'),
            data = json.dumps({'body':'new body'}))
        self.assertEqual(response.status_code,204)
        self.assertEqual(response.headers.get('Location'),url)
        self.assertEqual(response.headers.get('newBody'),'new body')

        # this will try to change the subject post when not the author
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='peggy@example.com',role=r,password='cat',confirmed=True)
        db.session.add(u)
        db.session.commit()
        response = self.client.put(
            url,
            headers = self.get_api_headers('peggy@example.com','cat'),
            data = json.dumps({'body':'new body'}))
        self.assertEqual(response.status_code,403)


    # This will test the token functions
    def test_auth_token(self):
        self.add_user()

        # This will get the token
        response = self.client.post(
            '/api/v1/tokens/',
            headers = self.get_api_headers('john@example.com','cat')
            )
        json_response = json.loads(response.get_data(as_text=True))
        token = json_response['token']

        # Now to use it to access the posts page
        response = self.client.get(
            '/api/v1/posts/',
            headers = self.get_api_headers(token,'')
            )
        self.assertEqual(response.status_code,200)

        # This will make sure you cannot use a token to get a token
        response = self.client.post(
            '/api/v1/tokens/',
            headers = self.get_api_headers(token,'')
            )
        self.assertEqual(response.status_code,401)


    # This will test the comment section of the api.
    def test_comment(self):
        self.add_user()

        # First to write a post to comment on
        response = self.client.post(
            '/api/v1/posts/',
            headers = self.get_api_headers('john@example.com','cat'),
            data = json.dumps({'body':'body of the blog post'}))
        self.assertEqual(response.status_code,201)
        url = response.headers.get('Location') + '/comments/'
        self.assertIsNotNone(url)

        # Test writing comments
        response = self.client.post(
            url,
            headers = self.get_api_headers('john@example.com','cat'),
            data = json.dumps({'body':'comment body'})
            )
        self.assertEqual(response.status_code,201)
        url = response.headers.get('Location')

        # Test getting comments
        response = self.client.get(
            '/api/v1/comments/',
            headers = self.get_api_headers('john@example.com','cat'))
        self.assertEqual(response.status_code,200)

        # Testing getting specific comments
        response = self.client.get(
            url,
            headers = self.get_api_headers('john@example.com','cat')
            )
        self.assertEqual(response.status_code,200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['body'],'comment body')


    # This will test the user api functions.
    def test_user(self):
        self.add_user()
        u = User.query.filter_by(email='john@example.com').first()

        # get the user's page
        response = self.client.get(
            f'/api/v1/users/{u.id}',
            headers = self.get_api_headers('john@example.com','cat')
            )
        self.assertEqual(response.status_code,200)

        # Create a post from the user
        response = self.client.post(
            '/api/v1/posts/',
            headers = self.get_api_headers('john@example.com','cat'),
            data = json.dumps({'body':'body of the blog post'}))
        self.assertEqual(response.status_code,201)

        # get the post
        response = self.client.get(
            f'/api/v1/users/{u.id}/posts/',
            headers = self.get_api_headers('john@example.com','cat')
            )
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['posts'][0]['body'],'body of the blog post')

        # get the users timeline, which should have their post
        response = self.client.get(
            f'/api/v1/users/{u.id}/timeline/',
            headers = self.get_api_headers('john@example.com','cat')
            )
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['posts'][0]['body'],'body of the blog post')
