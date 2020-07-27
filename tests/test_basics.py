import unittest
from flask import current_app
from app import create_app, db

# Quick notes about unittest:
#   setUp will run first
#   tearDown will run last
#       This is standard unittest terminology
#   anything with a test in front will run as a test
#
#   Run test via "flask test" in the cmdLine


class BasicTestCase(unittest.TestCase):
    # Runs first, creates db and context
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    # Runs last, removes the db and app context
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # Here is where the actual test is.
    # Must be structured "test_name" in order for unittest to recognize it.
    # Each test will run, and will return the logic statement which is not True
    #   in the terminal the test is started from.
    # All tests will run, and the results will be displayed at the end.
    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'],'Display this if wrong')

    # This is an example for testing certain errors come up.
    def test_errorShit(self):
        with self.assertRaises(TypeError):
            'l' + 0
