import json
import unittest.mock

from django.conf import settings
from django.test import TestCase
import requests_mock

from rime import models

from .helpers import obfuscate, PreAuthMixin


class TestResourceBase(PreAuthMixin, TestCase):
    endpoint = '/resources/'
    model = models.Resource

    def setUp(self):
        super().setUp()
        self.site_id = 'asdf'
        self.creds = models.Credential.objects.create(
            name='asdf',
            site=self.site_id,
            user=self.user,
            credentials=obfuscate({'data': 'data'}),
        )

    def test_create_no_hints(self):
        response = self.rfclient.post(self.endpoint, format='json', data={
        })
        self.assertEquals(response.status_code, 400)

    def test_create_no_cred(self):
        response = self.rfclient.post(self.endpoint, format='json', data={
            'hints': {
                'implementation': '12345123-1234-5213-1532-123412341234',
            },
        })
        self.assertEquals(response.status_code, 400)

    def test_create_no_impl(self):
        response = self.rfclient.post(self.endpoint, format='json', data={
            'hints': {
                'credentials': self.creds.id,
            },
        })
        self.assertEquals(response.status_code, 400)

    @requests_mock.mock()
    def test_create(self, mock_req):
        imp_id = '12345123-1234-5213-1532-123412341234'

        mock_req.get(settings.DIBBS['urls']['ar'] + '/implementations/{}/'.format(imp_id),
        text=json.dumps({
            'site': self.site_id,
            'appliance': 'app_x',
            'script': 'hello, world'
        }))

        with unittest.mock.patch.object(models.Cluster, 'do_create', return_value=None) as mock_method:
            response = self.rfclient.post(self.endpoint, format='json', data={
                'hints': {
                    'implementation': imp_id,
                    'credentials': self.creds.id,
                },
            })
            self.assertEquals(response.status_code, 201, response.content)
            mock_method.assert_called()
