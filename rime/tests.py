import base64
import json
import unittest.mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
import requests_mock
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APIClient

from . import models
from . import openstack


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


class TestOpenstackKeystone(TestCase):
    def test_session_create(self):
        credentials = {
            'username': 'red',
            'password': 'green',
            'project_name': 'blue',
            'auth_url': 'http://localhost:44000/v3'
        }
        session = openstack.keystone_session(credentials)

OS_RETURNS = [
{
    'url': 'http://localhost:45000/v2.0',
    'method': 'get',
    'return': {
        'text': (
            '{"version": {"status": "stable", "updated": "2014-04-17T00:00:00Z", "m'
            'edia-types": [{"base": "application/json", "type": "application/vnd.op'
            'enstack.identity-v2.0+json"}], "id": "v2.0", "links": [{"href": "http:'
            '//localhost:45000/v2.0/", "rel": "self"}, {"href": "http://docs.openst'
            'ack.org/", "type": "text/html", "rel": "describedby"}]}}'
        ),
    },
},
{
    'url': 'http://localhost:45000/v2.0/tokens',
    'method': 'post',
    'return': {
        'text': (
            '{"access":{"metadata":{"is_admin":0,"roles":["000000000000000000000000'
            '00000000"]},"serviceCatalog":[{"endpoints":[{"adminURL":"http://10.20.'
            '111.249:8774/v2/0000000000000000000000000000000f","id":"00000000000000'
            '00000000000000000e","internalURL":"http://10.20.111.249:8774/v2/000000'
            '0000000000000000000000000f","publicURL":"http://localhost:48774/v2/000'
            '0000000000000000000000000000f","region":"regionOne"}],"endpoints_links'
            '":[],"name":"nova","type":"compute"},{"endpoints":[{"adminURL":"http:/'
            '/10.20.111.249:5000/v3","id":"00000000000000000000000000000001","inter'
            'nalURL":"http://10.20.111.249:5000/v3","publicURL":"http://localhost:4'
            '5000/v3","region":"regionOne"}],"endpoints_links":[],"name":"keystonev'
            '3","type":"identityv3"},{"endpoints":[{"adminURL":"http://10.20.111.24'
            '9:8774/v3","id":"00000000000000000000000000000002","internalURL":"http'
            '://10.20.111.249:8774/v3","publicURL":"http://localhost:48774/v3","reg'
            'ion":"regionOne"}],"endpoints_links":[],"name":"novav3","type":"comput'
            'ev3"},{"endpoints":[{"adminURL":"http://10.20.111.249:9292","id":"0000'
            '0000000000000000000000000003","internalURL":"http://10.20.111.249:9292'
            '","publicURL":"http://localhost:49292","region":"regionOne"}],"endpoin'
            'ts_links":[],"name":"glance","type":"image"},{"endpoints":[{"adminURL"'
            ':"http://10.20.111.249:8777","id":"00000000000000000000000000000004","'
            'internalURL":"http://10.20.111.249:8777","publicURL":"http://localhost'
            ':48777","region":"regionOne"}],"endpoints_links":[],"name":"ceilometer'
            '","type":"metering"},{"endpoints":[{"adminURL":"http://10.20.111.249:6'
            '385","id":"00000000000000000000000000000005","internalURL":"http://10.'
            '20.111.249:6385","publicURL":"http://localhost:46385","region":"region'
            'One"}],"endpoints_links":[],"name":"ironic","type":"baremetal"},{"endp'
            'oints":[{"adminURL":"http://10.20.111.249:8004/v1/00000000000000000000'
            '000000000066","id":"00000000000000000000000000000006","internalURL":"h'
            'ttp://10.20.111.249:8004/v1/00000000000000000000000000000066","publicU'
            'RL":"http://localhost:48004/v1/00000000000000000000000000000066","regi'
            'on":"regionOne"}],"endpoints_links":[],"name":"heat","type":"orchestra'
            'tion"},{"endpoints":[{"adminURL":"http://10.20.111.206:7480/swift/v1",'
            '"id":"00000000000000000000000000000007","internalURL":"http://10.20.11'
            '1.206:7480/swift/v1","publicURL":"http://localhost:47480/swift/v1","re'
            'gion":"regionOne"}],"endpoints_links":[],"name":"swift","type":"object'
            '-store"},{"endpoints":[{"adminURL":"http://10.20.111.249:1234/v1","id"'
            ':"00000000000000000000000000000008","internalURL":"http://10.20.111.24'
            '9:1234/v1","publicURL":"http://localhost:41234/v1","region":"regionOne'
            '"}],"endpoints_links":[],"name":"blazar","type":"reservation"},{"endpo'
            'ints":[{"adminURL":"http://10.20.111.249:35357/v2.0","id":"00000000000'
            '000000000000000000009","internalURL":"http://10.20.111.249:35357/v2.0"'
            ',"publicURL":"http://localhost:45000/v2.0","region":"regionOne"}],"end'
            'points_links":[],"name":"keystone","type":"identity"},{"endpoints":[{"'
            'adminURL":"http://10.20.111.249:9696","id":"00000000000000000000000000'
            '00000a","internalURL":"http://10.20.111.249:9696","publicURL":"http://'
            'localhost:49696","region":"regionOne"}],"endpoints_links":[],"name":"n'
            'eutron","type":"network"}],"token":{"audit_ids":["AAAAAAAAAAAAAAAAAAAA'
            'AA"],"expires":"3017-03-15T22:00:53Z","id":"00000000000000000000000000'
            '00000b","issued_at":"2017-03-15T21:00:53.371933","tenant":{"descriptio'
            'n":".","enabled":true,"id":"0000000000000000000000000000000c","name":"'
            'Chameleon"}},"user":{"id":"0000000000000000000000000000000d","name":"n'
            'timkovi","roles":[{"name":"_member_"}],"roles_links":[],"username":"nt'
            'imkovi"}}}'
        )
    },
},
{
    'url': 'http://localhost:48004/v1/00000000000000000000000000000066/stacks',
    'method': 'get',
    'return': {
        'text': (
            '{"stacks": []}'
        )
    },
},
]

class TestOpenstackHeat(TestCase):
    def setUp(self):
        self.creds = {
            'username': 'red',
            'password': 'green',
            'project_name': 'blue',
            'auth_url': 'http://localhost:45000/v2.0'
        }
        self.session = openstack.keystone_session(self.creds)
        self.hc = openstack.heat_client(session=self.session)
        self.key = self.creds['auth_url']

    @requests_mock.mock()
    def test_heat_client(self, m):
        for rr in OS_RETURNS:
            getattr(m, rr['method'])(rr['url'], **rr['return'])
        # m.post(self.key + '/auth/tokens', text=json.dumps({}))

        list(self.hc.stacks.list())


from rime.views import ClusterViewSet

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

        with unittest.mock.patch.object(ClusterViewSet, 'perform_create', return_value=None, side_effect=side_effect) as mock_method:
            response = self.rfclient.post(self.endpoint, format='json', data={
                'site': site_id,
                'credential': self.cred.id,
                'implementation': imp_id,
            })
            assert response.status_code == 201, (response.status_code, response.content)
            mock_method.assert_called()
