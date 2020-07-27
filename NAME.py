# This file is run as the flask app.

# importing used modules
import os

# This is used to determine which parts of the app are being tested.
# If this is not above the rest of the test functions, you will not get a good report
COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    # This stats the coverage engine
    # Branch applies that it will tell you if each true and false path is
    #   exercised both ways.
    # includes limits it to files that are in the app package.
    #   i.e., do not include venv/tests
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()


import sys

import click


# from the app folder __init__.py
# This will be used to create an context of the app with a given configuration
from app import create_app, db

 # from the model folder in the app folder
 # This will be used to create the database for the application
from app.models import User, Role, Permission, Post, Follow, Comment

# Necessary to create the migration folder.
from flask_migrate import Migrate, upgrade

# this CREATES THE CONTEXT of the application using the environmental variable
# i.e. this runs the app, i.e. the APP FACTORY
app = create_app(os.getenv('FLASK_CONFIG') or 'default')

# This is used in via the terminal to create the migration scripts automatically
migrate = Migrate(app,db)

# This defines the database to be used if you start a flask shell
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Permission=Permission, Post=Post,
                Follow=Follow, Comment=Comment)

# This runs the tests.
# run from terminal via "flask test" (thats the function name), results will
# display in terminal.
@app.cli.command()
def test():
    """Run the unit tests."""

    import unittest
    # This will search the tests directory, and run test_files and test_functions
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


# This command is run in terminal by "flask test --coverage"
# This will print out a summary of the tests that were run, and provide you
#   with a percentage of coverage
@app.cli.command()
@click.option('--coverage/--no-coverage',default=False,
    help='Run tests under code coverage.')
def test(coverage):
    """Run the unit tests"""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable,[sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


# This is used to determine what parts of the app are slow.
# I couldnt get the app instance to run
@app.cli.command()
@click.option('--length',default=25,
                help='Number of cuntions to include in the profiler report.')
@click.option('--profile_dir',default=None,
                help='Directory where profiler data files are saved.')
def profile(length,profile_dir):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app,restrictions=[length],
            profile_dir=profile_dir)
    app.run(debug=False)


# This section is for items particular to deploying a production app
# These functions will run what you need to create the app on a new server
@app.cli.command()
def deploy():
    """Run deployment tasks."""

    # Migrate the database to the latest revision
    upgrade()

    # Create/update user roles
    Role.insert_roles()

    # Ensure all users follow themselves
    User.add_self_follows()



# This just shows an example of running flask functions from the terminal
# run via flask fuckyeah --trythis for True or flask fuckyeah --no-dont for False
# Default flask fuckyeah will run it for True
@app.cli.command()
@click.option('--trythis/--no-dont',default=True,help='None')
def fuckyeah(trythis):
    if trythis:
        print('trythis')
    else:
        print('Didn\'t do it')
