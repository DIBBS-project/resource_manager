import contextlib
import json

from flask import Flask, jsonify, request

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


@app.route('/sites/<id>/', methods=['GET'])
def site(id):
    return jsonify(app.config.sites[id])


@app.route('/appliances/<id>/', methods=['GET'])
def appliance(id):
    return jsonify(app.config.apps[id])


@app.route('/implementations/<id>/', methods=['GET'])
def implementation(id):
    return jsonify(app.config.imps[id])
