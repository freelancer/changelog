import flask
import json


def json_response(result=None, message=None, status_code=200):
    response = {}

    if 200 <= status_code <= 299:
        # All 2xx status codes are success.
        response['status'] = 'success'
    elif 400 <= status_code <= 599:
        response['status'] = 'error'

    if result:
        response['result'] = result
    if message:
        response['message'] = message

    return flask.current_app.response_class(
        response=json.dumps(
            response
        ),
        mimetype='application/json',
        status=status_code
    )
