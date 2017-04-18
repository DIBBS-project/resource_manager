import base64
import json

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


def obfuscate(data):
    return base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')


class PreAuthMixin(object):
    def setUp(self):
        User = get_user_model()
        self.rfclient = APIClient()

        username = 'bob'
        password = 'BOB'
        self.user = User.objects.create_superuser(
            username,
            '{}@example.com'.format(username),
            password,
        )

        self.rfclient.force_authenticate(user=self.user)
