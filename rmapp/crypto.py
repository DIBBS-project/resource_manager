# coding: utf-8
from __future__ import absolute_import, print_function

import base64
import json

from Crypto.PublicKey import RSA


def decrypt_credentials(encrypted_credentials, profile):
    # Use the private key de temporarily decrypt and check that it gives JSON
    key = RSA.importKey(profile.rsa_key)

    to_decrypt = base64.b64decode(encrypted_credentials)
    decrypted_credentials = key.decrypt(to_decrypt)

    # Temporary fix
    # TODO: Understand why there are additional characters at the beginning and fix this hack
    pos = decrypted_credentials.rfind('{')
    print(pos)
    decrypted_credentials = decrypted_credentials[decrypted_credentials.rfind('{'):]
    decrypted_credentials = json.loads(decrypted_credentials)
    return decrypted_credentials
