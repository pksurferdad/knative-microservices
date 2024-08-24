import json
import os
import requests
import flask
from flask import Flask, request, jsonify
from flask.logging import create_logger
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException

# flask app configuration
app = Flask(__name__)
log = create_logger(app)
log.setLevel(os.environ.get('LOG_LEVEL', 'DEBUG'))

@app.route('/', methods=['POST'])
def main():
    # process the event message delivered by the event broker
    event_message = request.get_json(force=True)

    # do something with the event message
    log.info('Received event message: {}'.format(json.dumps(event_message)))

    response = {
    'success' : True,
    'message' : 'Message successfully processed!'
    }

    return jsonify(response), 200
    

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    log.error('HTTP Exception: {}'.format(e))
    response = {
        'success': False,
        'error': {
            'type': e.name,
            'message': e.description,
        }
    }    # replace the body with JSON
    return jsonify(response), e.code


@app.errorhandler(RuntimeError)
def handle_runtime_error(error):
    message = [str(x) for x in error.args]
    log.error(message)
    response = {
        'success': False,
        'error': {
            'type': error.__class__.__name__,
            'message': message
        }
    }

    return jsonify(response), 422


@app.errorhandler(Exception)
def unhandled_exception(error):
    log.error('Unhandled Exception: {}'.format(error))
    response = {
        'success': False,
        'error': {
            'type': error.__class__.__name__,
            'message': 'An unexpected error has occurred.',
        }
    }

    return jsonify(response), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
