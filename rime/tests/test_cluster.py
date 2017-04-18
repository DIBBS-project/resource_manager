import json
import unittest.mock

from django.conf import settings
from django.test import TestCase
import requests_mock

from rime import models
from rime.views import ClusterViewSet

from .helpers import obfuscate, PreAuthMixin


class TestClusterBase(PreAuthMixin, TestCase):
    endpoint = '/clusters/'
    model = models.Cluster

    def setUp(self):
        super().setUp()

        self.cred = models.Credential.objects.create(
            name='asdf',
            site='some-site-id',
            user=self.user,
            credentials=obfuscate({'username': 'lion', 'password': 'tiger', 'project_name': 'bear'}),
        )


class TestClusterObject(TestClusterBase):
    def test_create(self):
        self.model.objects.create(
            root_owner=self.user,
            credential=self.cred,
            implementation='adsf',
        )


class TestClusterCreationSerialization(TestClusterBase):
    @requests_mock.mock()
    def test_create(self, m):#, mcvs):
        imp_id = 'impl_x'
        site_id = self.cred.site
        keystone = 'http://localhost:44000/v3'

        m.get(settings.DIBBS['urls']['ar'] + '/implementations/{}/'.format(imp_id), text=json.dumps({
            'site': site_id,
            'appliance': 'app_x',
        }))
        m.get(settings.DIBBS['urls']['ar'] + '/sites/{}/'.format(site_id), text=json.dumps({
            'api_url': keystone,
        }))
        # m.post(keystone + '/auth/tokens', text=json.dumps({}))

        def side_effect(serializer):
            serializer.save(root_owner=self.user) # mock_method doesn't give self, so go out-of-band

        with unittest.mock.patch.object(ClusterViewSet, 'perform_create', return_value=None, side_effect=side_effect) as mock_method:#, \
                # self.settings(CELERY_ALWAYS_EAGER=True):
            response = self.rfclient.post(self.endpoint, format='json', data={
                'site': site_id,
                'credential': self.cred.id,
                'implementation': imp_id,
            })
            assert response.status_code == 201, (response.status_code, response.content)
            mock_method.assert_called()
