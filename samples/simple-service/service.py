import json
import os
import flask
from flask import Flask, request, jsonify
from flask.logging import create_logger
from werkzeug.exceptions import HTTPException

# flask app configuration
app = Flask(__name__)
log = create_logger(app)
log.setLevel(os.environ.get('LOG_LEVEL', 'DEBUG'))

# Implement the main route of our application
@app.route('/', methods=['GET','POST'])
def main():

  # stuff your service does
  
  return 'Your knative service completed successfully!', 200

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    log.error('HTTP Exception: %s', (e))
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
    log.error('Unhandled Exception: %s', (error))
    response = {
        'success': False,
        'error': {
            'type': error.__class__.__name__,
            'message': 'An unexpected error has occurred.',
        }
    }

    return jsonify(response), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))