from django.conf import settings
import requests


def implementation(name):
    url = settings.DIBBS['urls']['ar'] + '/implementations/{}/'.format(name)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def site(name):
    url = settings.DIBBS['urls']['ar'] + '/sites/{}/'.format(name)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
