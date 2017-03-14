#!/usr/bin/env python
"""
Test the Django service
"""
import json
import pathlib
import sys
import time

import requests

from common_dibbs.names import AUTHORIZATION_HEADER

from sham_ar import app as sham_ar
from sham_cas import app as sham_cas
from helpers import FlaskAppManager


TEST_DIR = pathlib.Path(__file__).resolve().parent
BASE_DIR = TEST_DIR.parent

ROOT = 'http://localhost:8002'
CAS_URL = 'http://localhost:7000'
AR_URL = 'http://localhost:8003'

ALICE_VALID = {AUTHORIZATION_HEADER: 'alice,1'}
ALICE_INVALID = {AUTHORIZATION_HEADER: 'alice,0'}


def assertStatus(response, expected, message=None):
    try:
        start, stop = expected
    except TypeError:
        if response.status_code == expected:
            return
    else:
        if start <= response.status_code < stop:
            return
        expected = '[{}, {})'.format(start, stop)

    if message:
        print(message, file=sys.stderr)

    print('Received status {}, expected {}\n-------------\n{}'
        .format(response.status_code, expected, response.content),
        file=sys.stderr)

    raise AssertionError(message or "bad status code")


def test(ar=None, cas=None):
    ar_sites = ar.app.config.sites = {}
    # sanity check root
    response = requests.get(ROOT)
    assertStatus(response, 200)

    # # check with auth
    # response = requests.get(ROOT, headers=ALICE_VALID)
    # assertStatus(response, 200)

    # put a credential for a site
    SITE = 'some-site-id'
    ar_sites[SITE] = {'url': 'something'}
    response = requests.post(ROOT + '/credentials/', json={
        'site': SITE,
        'name': 'me@site',
        'credentials': json.dumps({'username': 'magic', 'password': 'johnson'}),
    })
    assertStatus(response, 403, 'auth required')

    response = requests.post(ROOT + '/credentials/', headers=ALICE_VALID, json={
        'site': SITE,
        'name': 'me@site',
        'credentials': json.dumps({'username': 'magic', 'password': 'johnson'}),
    })
    assertStatus(response, 201)
    credentials = response.json()
    assert all(key in credentials for key in ['id', 'created', 'site', 'user'])
    assert not any(key in credentials for key in ['credentials'])
    cred_id = credentials['id']

    # - site must exist
    response = requests.post(ROOT + '/credentials/', headers=ALICE_VALID, json={
        'site': 'non-existant',
        'name': 'me@site2',
        'credentials': json.dumps({'username': 'magic', 'password': 'johnson'}),
    })
    assertStatus(response, (400, 500), 'error on nonexistant site')

    # make sure it's a black hole for the user (can't get back plaintext or raw hash)
    response = requests.get(ROOT + '/credentials/{}/'.format(cred_id))
    assertStatus(response, 200)
    credentials = response.json()
    assert 'credentials' not in credentials

    # post cluster
    response = requests.post(ROOT + '/resources/', headers=ALICE_VALID, json={
        'credential': cred_id,
        'site': SITE,
    })
    assertStatus(response, 201)


def self_test():
    requests.get(CAS_URL + '/auth/tokens', headers=ALICE_INVALID)
    requests.get(AR_URL)


def main(argv=None):
    with FlaskAppManager(sham_cas, port=7000) as cas, \
            FlaskAppManager(sham_ar, port=8003) as ar:
        self_test()
        return test(ar=ar, cas=cas)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
