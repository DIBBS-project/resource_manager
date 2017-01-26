# coding: utf-8
from __future__ import absolute_import, print_function

import base64
import json

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA


RSA_KEY_LENGTH = 1024


def decrypt_credentials(encrypted_credentials, rsa_key):
    """
    Use the private key to decrypt and decode the credentials from
    base64 cyphertext to a JSON object.
    """
    key = RSA.importKey(rsa_key)
    cipher = PKCS1_OAEP.new(key)
    cipher_text = base64.b64decode(encrypted_credentials)
    message = cipher.decrypt(cipher_text)

    # Temporary fix
    # TODO: Understand why there are additional characters at the beginning and fix this hack
    pos = message.rfind('{')
    print(pos)
    message = message[message.rfind('{'):]

    return json.loads(message)


def generate_rsa_key():
    return RSA.generate(RSA_KEY_LENGTH).exportKey()


def private_to_public(private_key):
    key = RSA.importKey(private_key)
    return key.publickey().exportKey()
