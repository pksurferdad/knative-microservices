import json
import os
import requests
import flask
from flask import Flask, request, jsonify
from flask.logging import create_logger
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException
from cloudevents.http import CloudEvent, to_structured

# flask app configuration
app = Flask(__name__)
log = create_logger(app)
log.setLevel(os.environ.get('LOG_LEVEL', 'DEBUG'))


# environment variables
broker_url = os.environ.get('BROKER_URL', None)

@app.route('/', methods=['POST'])
def main():
    # process the request message and send it to the knative broker
    event_headers = request.headers
    event_message = request.get_json(force=True)

    required_headers = ['ce_type', 'ce_source']
    missing_headers = [header for header in required_headers if header not in event_headers]

    if missing_headers:
        log.debug(f'event message: {event_message}')
        raise RuntimeError(f'Message cannot be processed. Missing required event headers: {", ".join(missing_headers)}')

    # build the event and http request
    attributes = {
        'type' : event_headers['ce_type'],
        'source' : event_headers['ce_source']
    }

    event = CloudEvent(attributes,event_message)
    headers, body = to_structured(event)

    resp = requests.post(broker_url,
                         headers=headers,
                         data=body)
    
    if resp.status_code != 202:
        raise RuntimeError(str(resp.status_code) + ' ' + resp.text)
    
    log.info("sent message for event: {}. broker response: response code {} response text {}".format(event_headers['ce_type'],resp.status_code, resp.text))
    
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
