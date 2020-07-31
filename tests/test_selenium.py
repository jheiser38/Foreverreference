# I HAVE NOT GOTTEN THIS TEST TO WORK
# The app contexxt for testing is not allowed to run itself.
# See github for potential fixes Miguel Grinberg mentions.

from selenium import webdriver
import re
import unittest
from app import create_app, db
from app import fake
from app.models import Role, User
from threading import Thread
from flask import url_for, current_app
import time


class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        # start chrome
        options = webdriver.ChromeOptions()
        #options.add_argument('headless')
        # THIS NEEDS TO BE ADDED TO THE SHELL PATH VIA THE FOLLOWING
        # PATH = $PATH:/mnt/c/Users/jheis/documents/flaskwebdevelopment/environments/chromedriver.exe
        uri = '/mnt/c/Users/jheis/documents/flaskwebdevelopment/environments/chromedriver.exe'
        try:
            cls.client = webdriver.Chrome(uri)
        except:
            pass

        # Skip these test if the browser could not be started
        if cls.client:
            # create the application
            cls.app = create_app('testing')
            print (cls.app.config['SQLALCHEMY_DATABASE_URI'])
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # suppress logging to keep unittest output clean
            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            # create the database and populate with some fake data
            db.create_all()
            Role.insert_roles()
            fake.users(10)
            fake.posts(10)

            # add an administrator
            print('you here ho')
            admin_role = Role.query.filter_by(name='administrator').first()
            admin = User(role = admin_role,\
                         email = 'john@example.com',\
                         password = 'cat',\
                         confirmed = True,\
                         username = 'john')
            db.session.add(admin)
            db.session.commit()

            # start the flask server in the thread
            print('Defining the thread')
            cls.server_thread = Thread(target = cls.app.run,kwargs={'debug':False})
            print('Running the thread')
            if __name__ == "__main__":
                cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # stop the Flask server and the browser
            cls.client.get('http://localhost:5000/shutdown')
            cls.client.quit()
            cls.server_thread.join()

            # destroy database
            #db.drop_all()
            #db.session.remove()

            #remove the application context
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    # This test will navigate to the homepage, fill out the login form, and login
    # CURRENTLY DOES NOT EXECUTE, DOES NOT GET THE APP CONTEXT
    def dtest_admin_home_page(self):
        # Navigate to the home page
        self.client.get('http://localhost:5000/') # Navigate to a url
        #self.assertIn('Please Login',self.client.page_source)

        # navigation to the login page happens automatically
        # log in
        #time.sleep(10)
        self.client.find_element_by_name('email').send_keys('john@example.com')
            #elements are defined in the auth/forms.py
        #time.sleep(10)
        self.client.find_element_by_name('password').send_keys('cat')
        #time.sleep(10)
        self.client.find_element_by_name('submit').click() # clicks a link
        #time.sleep(10)
        self.assertIn('Home Page',self.client.page_source)
