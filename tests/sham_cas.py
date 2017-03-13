import contextlib
import json

from flask import Flask, request

from common_dibbs.names import AUTHORIZATION_HEADER
assert not AUTHORIZATION_HEADER.startswith('HTTP')

app = Flask(__name__)


@app.route('/')
def root():
    return repr(dict(app.config))


@app.route('/_shutdown', methods=['POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return 'Server shutting down...'


@app.route('/auth/tokens', methods=['GET'])
def validate_fake_token():
    try:
        username, valid = request.headers[AUTHORIZATION_HEADER].split(',')
    except KeyError:
        return json.dumps({'error': 'missing token'}), 400
    if int(valid):
        return json.dumps({'username': username}), 200
    else:
        return json.dumps({'error': 'unauthorized'}), 403
