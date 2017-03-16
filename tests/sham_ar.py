import contextlib
import json

from flask import Flask, jsonify, request

from common_dibbs.names import AUTHORIZATION_HEADER
assert not AUTHORIZATION_HEADER.startswith('HTTP')

app = Flask(__name__)


def keyerror_404(mapping, key):
    try:
        return jsonify(mapping[key])
    except KeyError:
        response = jsonify({'error': 'key not found'})
        response.status_code = 404
        return response


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


@app.route('/sites/<id>/', methods=['GET'])
def site(id):
    return keyerror_404(app.config.sites, id)
    # try:
    #     return jsonify(app.config.sites[id])
    # except KeyError:
    #     response = jsonify({})
    #     response.status_code = 404
    #     return response


@app.route('/appliances/<id>/', methods=['GET'])
def appliance(id):
    return keyerror_404(app.config.apps, id)


@app.route('/implementations/<id>/', methods=['GET'])
def implementation(id):
    return keyerror_404(app.config.imps, id)
