# This file will be used to house all email functionality.

# allows for creating multiple threads too allow for sending an email without
# keeping you on the page (seemless UI)
from threading import Thread
# Allows using the context of the app to run the mail object.
from flask import current_app
from flask import render_template
# allows for creating a message object which can then be sent
from flask_mail import Message
# from the parent directory (app), import the mail object
from . import mail

# This function will allows for sending emails while loading a browser.
def send_async_email(app, msg):
    # Flask-mail uses the current_app to send mail, so it must be passed in
    with app.app_context():
        # standard format to send a messageS
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    """
        This function makes for easy email generation.
        to is a target email/list of emails,
        subject is the actual subject of the email,
        and the body is a rendered html file or txt if you're barbarian.
        The kwargs are passed to the html file generation.
    """
    # gets the current app context in order to run flask-mails send function
    app = current_app._get_current_object()
    # here is another method to update the config settings.
    # app.config.update(MAIL_SERVER='smtp.googlemail.com')
    # this creates the mail message:
    #   first arg - subject
    #   sender arg - sender email address (admin)
    #   recipients arg - list of emails to send to
    msg = Message(app.config['MAIL_PREFIX'] + ' ' + subject,
                  sender=app.config['MAIL_SENDER'], recipients=[to])
    # The difference between the body of the email and the html, is
    #   that the body will not display if the HTML is assigned.
    # In the view function, the template will be mail/templatename, with no suffix
    # so that it can grab the txt and html files if assigned.
    # The args passed in will be used to render the template.
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    # This must be used to create a thread which will send the email.
    thr = Thread(target=send_async_email, args=[app, msg])
    # This starts the individual thread to send the email.
    thr.start()
    #
    return thr
