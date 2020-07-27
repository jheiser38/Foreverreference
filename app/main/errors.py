from flask import render_template, jsonify, request
from . import main

#   Note these are app_errorhandlers vice errorhandlers.
#   This means that they will be invoked app wide vice in the blueprint
@main.app_errorhandler(404)
def page_not_found(e):

    # This portion will return a json version if the request header specifies
    #   that it will only take json type data.
    # Browsers do not typically specify any restrictions on response format,
    #   but API clients do.
    # If html is not in the requested formats, and json is, it will return json.
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error':'not found'})
        response.status_code = 404
        return response

    # Otherwise:
    # Renders the template, and provides the error code as the second arguement.
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500


@main.app_errorhandler(403)
def forbidden(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    return render_template('403.html'), 403
