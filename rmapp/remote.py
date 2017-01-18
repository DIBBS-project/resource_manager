# coding: utf-8
from __future__ import absolute_import, print_function

from django.conf import settings

from common_dibbs.clients.ar_client.apis.appliances_api import AppliancesApi
from common_dibbs.clients.ar_client.apis.appliance_implementations_api import ApplianceImplementationsApi
from common_dibbs.clients.ar_client.apis.scripts_api import ScriptsApi
from common_dibbs.clients.ar_client.apis.sites_api import SitesApi
from common_dibbs.clients.rpa_client.apis import ActionsApi

from common_dibbs.misc import configure_basic_authentication


def appliances_name(name):
    appliances_client = AppliancesApi()
    appliances_client.api_client.host = settings.DIBBS['urls']['ar']
    configure_basic_authentication(appliances_client, "admin", "pass")

    return appliances_client.appliances_name_get(name=name)


def actions_new_account(url_root):
    '''
    *url_root* must include the scheme and host, optionally the port.
    '''
    actions_api = ActionsApi()
    actions_api.api_client.host = url_root
    configure_basic_authentication(actions_api, "admin", "pass")

    return actions_api.new_account_post()


def sites_name_get(name):
    sites_client = SitesApi()
    sites_client.api_client.host = settings.DIBBS['urls']['ar']
    configure_basic_authentication(sites_client, "admin", "pass")

    return sites_client.sites_name_get(name=name)


def appliance_impl_name_get(name):
    appliance_implementations_client = ApplianceImplementationsApi()
    appliance_implementations_client.api_client.host = settings.DIBBS['urls']['ar']
    configure_basic_authentication(appliance_implementations_client, "admin", "pass")

    return appliance_implementations_client.appliances_impl_name_get(name=name)


def get_template_from_appliance_registry(appliance_impl_name, action_name):
    scripts_client = ScriptsApi()
    scripts_client.api_client.host = settings.DIBBS['urls']['ar']
    configure_basic_authentication(scripts_client, "admin", "pass")

    script = scripts_client.scripts_appliance_action_get(appliance_impl_name, action_name)
    # TODO fix
    print(script)
    return script.code


def appliances_name(name):
    appliances_client = AppliancesApi()
    appliances_client.api_client.host = settings.DIBBS['urls']['ar']
    configure_basic_authentication(appliances_client, "admin", "pass")

    return appliances_client.appliances_name_get(name)


def appliance_implementations():
    appliance_implementations_client = ApplianceImplementationsApi()
    appliance_implementations_client.api_client.host = settings.DIBBS['urls']['ar']
    configure_basic_authentication(appliance_implementations_client, "admin", "pass")

    return appliance_implementations_client.appliances_impl_get()


def appliances_impl_name_get(name):
    appliance_implementations_client = ApplianceImplementationsApi()
    appliance_implementations_client.api_client.host = settings.DIBBS['urls']['ar']
    configure_basic_authentication(appliance_implementations_client, "admin", "pass")

    return appliance_implementations_client.appliances_impl_name_get(name)


def sites():
    sites_client = SitesApi()
    sites_client.api_client.host = settings.DIBBS['urls']['ar']
    configure_basic_authentication(sites_client, "admin", "pass")

    return sites_client.sites_get()
