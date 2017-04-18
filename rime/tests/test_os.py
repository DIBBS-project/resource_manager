from django.test import TestCase
import requests_mock

from rime import models
from rime import openstack

# from .helpers import PreAuthMixin


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
