
import json
import requests
import os
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
KAFKA_SINK_URL = os.environ.get('KAFKA_SINK_URL', None)
headers = {'content-type': 'application/json'}

@app.route('/', methods=['POST'])
def main():
    # process the request message and send it to the knative kafka sink resource
    event_headers = request.headers
    event_message = request.get_json(force=True)

    # do something with the event message
    log.info('event message: {}'.format(event_message))
    
    # build the event and http request
    attributes = {
        'type' : 'dev.kafka.type',
        'source' : 'dev.kafka.source'
    }

    event = CloudEvent(attributes,event_message)
    headers, body = to_structured(event)

    # send the event to the kafka-sink-url
    resp = requests.post(KAFKA_SINK_URL, headers=headers, data=body)
    log.info('response code: {}'.format(resp.status_code))

    if resp.status_code != 202:
        raise RuntimeError(str(resp.status_code) + ' ' + resp.text)

    return '', 200
    

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


