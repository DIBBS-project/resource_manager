from heatclient.client import Client as HeatClient
import keystoneauth1 as ksa
import keystoneauth1.loading
import keystoneauth1.session
from novaclient.client import Client as NovaClient


REQUIRED_KEYS = {'auth_url', 'username', 'password', 'project_name'}


def heat_client(credentials=None, session=None):
    if session is None:
        session = keystone_session(credentials)
    return HeatClient("1", session=session)


def keystone_session(credentials):
    missing_keys = REQUIRED_KEYS - set(credentials)
    if missing_keys:
        raise ValueError('credentials missing required keys: {}'.format(missing_keys))

    loader = ksa.loading.get_plugin_loader('password')
    auth = loader.load_from_options(**credentials)
    sess = ksa.session.Session(auth=auth)
    return sess


def nova_client(credentials=None, session=None):
    if session is None:
        session = keystone_session(credentials)
    return NovaClient('2', session=session)
