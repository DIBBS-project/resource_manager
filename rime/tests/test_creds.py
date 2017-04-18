import json
import unittest.mock

from django.conf import settings
from django.test import TestCase
import requests_mock

from rime import models
from rime import openstack

from .helpers import obfuscate, PreAuthMixin



class TestCredentialBase(PreAuthMixin, TestCase):
    endpoint = '/credentials/'
    model = models.Credential


class TestCredentialObject(TestCredentialBase):
    def test_basic(self):
        # TODO should validation (e.g. that the site really exists) be for
        # object creation or serialization?
        self.model.objects.create(
            name='asdf',
            site='some-site-id',
            user=self.user,
            credentials=obfuscate({'data': 'data'}),
        )

    def test_deobfuscate(self):
        creds = {'data': 'data'}
        self.assertEqual(
            self.model(credentials=obfuscate(creds)).deobfuscated_credentials,
            creds
        )

class TestCredentialAccess(TestCredentialBase):
    def test_list(self):
        some_creds = self.model.objects.create(
            name='asdf',
            site='asdf',
            user=self.user,
            credentials=obfuscate({'data': 'data'}),
        )
        response = self.rfclient.get(self.endpoint)
        assert 200 <= response.status_code < 300, (response.status_code, response.content)
        rtext = response.content.decode(response.charset)
        data = json.loads(rtext)
        self.assertEqual(len(data), 1)

        self.model.objects.create(name='zxcv', site='zxcv', user=self.user, credentials='{}')
        self.assertEqual(len(self.rfclient.get(self.endpoint).json()), 2)

    @requests_mock.mock()
    def test_create(self, m):
        m.get(settings.DIBBS['urls']['ar'] + '/sites/a_site/', text='{}')
        response = self.rfclient.post(self.endpoint, format='json', data={
            'name': 'a_name',
            'site': 'a_site',
            'credentials': obfuscate({'username': 'lion', 'password': 'tiger', 'project_name': 'bear'})
        })
        assert response.status_code == 201, (response.status_code, response.content)

    @requests_mock.mock()
    def test_credential_fields(self, m):
        m.get(settings.DIBBS['urls']['ar'] + '/sites/a_site/', text='{}')
        response = self.rfclient.post(self.endpoint, format='json', data={
            'name': 'a_name',
            'site': 'a_site',
            'credentials': obfuscate({'pointless': 'field'})
        })
        assert response.status_code == 400
        data = response.json()
        assert 'credentials' in data
        assert 'missing' in data['credentials'][0].lower()

    @requests_mock.mock()
    def test_check_site_exists(self, m):
        m.get(settings.DIBBS['urls']['ar'] + '/sites/not_really_here/', status_code=404)
        response = self.rfclient.post(self.endpoint, format='json', data={
            'name': 'a_name',
            'site': 'not_really_here',
            'credentials': obfuscate({}),
        })
        assert 400 <= response.status_code < 500, (response.status_code, response.content)
