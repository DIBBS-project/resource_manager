# coding: utf-8
from __future__ import absolute_import, print_function

from django.conf import settings

from common_dibbs.auth import swagger_basic_auth
from common_dibbs.clients.ar_client.apis.appliances_api import AppliancesApi
from common_dibbs.clients.ar_client.apis.appliance_implementations_api import ApplianceImplementationsApi
from common_dibbs.clients.ar_client.apis.scripts_api import ScriptsApi
from common_dibbs.clients.ar_client.apis.sites_api import SitesApi
from common_dibbs.clients.rpa_client.apis import ActionsApi
from common_dibbs.django import get_request, relay_swagger


def appliances_name(name):
    appliances_client = AppliancesApi()
    appliances_client.api_client.host = settings.DIBBS['urls']['ar']
    relay_swagger(appliances_client, get_request())

    return appliances_client.appliances_name_get(name=name)


def actions_new_account(url_root):
    '''
    *url_root* must include the scheme and host, optionally the port.
    '''
    actions_api = ActionsApi()
    actions_api.api_client.host = url_root
    # relay_swagger(actions_api, get_request())
    swagger_basic_auth(actions_api, "admin", "pass")

    return actions_api.new_account_post()


def sites_name_get(name):
    sites_client = SitesApi()
    sites_client.api_client.host = settings.DIBBS['urls']['ar']
    relay_swagger(sites_client, get_request())

    return sites_client.sites_name_get(name=name)


def appliance_impl_name_get(name):
    appliance_implementations_client = ApplianceImplementationsApi()
    appliance_implementations_client.api_client.host = settings.DIBBS['urls']['ar']
    relay_swagger(appliance_implementations_client, get_request())

    return appliance_implementations_client.appliances_impl_name_get(name=name)


def get_template_from_appliance_registry(appliance_impl_name, action_name):
    scripts_client = ScriptsApi()
    scripts_client.api_client.host = settings.DIBBS['urls']['ar']
    relay_swagger(scripts_client, get_request())

    script = scripts_client.scripts_appliance_action_get(appliance_impl_name, action_name)
    # TODO fix
    print(script)
    return script.code


def appliances_name(name):
    appliances_client = AppliancesApi()
    appliances_client.api_client.host = settings.DIBBS['urls']['ar']
    relay_swagger(appliances_client, get_request())

    return appliances_client.appliances_name_get(name)


def appliance_implementations():
    appliance_implementations_client = ApplianceImplementationsApi()
    appliance_implementations_client.api_client.host = settings.DIBBS['urls']['ar']
    relay_swagger(appliance_implementations_client, get_request())

    return appliance_implementations_client.appliances_impl_get()


def appliances_impl_name_get(name):
    appliance_implementations_client = ApplianceImplementationsApi()
    appliance_implementations_client.api_client.host = settings.DIBBS['urls']['ar']
    relay_swagger(appliance_implementations_client, get_request())

    return appliance_implementations_client.appliances_impl_name_get(name)


def sites():
    sites_client = SitesApi()
    sites_client.api_client.host = settings.DIBBS['urls']['ar']
    relay_swagger(sites_client, get_request())

    return sites_client.sites_get()
