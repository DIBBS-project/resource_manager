#!/usr/bin/env python
"""
Test the Django service
"""
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


def test():
    # sanity check root
    response = requests.get(ROOT)
    assertStatus(response, 200)

    # check with auth
    response = requests.get(ROOT, headers=ALICE_VALID)
    assertStatus(response, 200)


def self_test():
    requests.get(CAS_URL + '/auth/tokens', headers=ALICE_INVALID)
    requests.get(AR_URL)


def main(argv=None):
    with FlaskAppManager(sham_cas, port=7000) as cas \
            FlaskAppManager(sham_ar, port=8003) as ar:
        self_test()
        return test()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
