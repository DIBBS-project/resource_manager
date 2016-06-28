def reset_data():
    pass


def create_infrastructure():
    from rpapp.models import Site

    sites_dict = {
        "KVM@TACC" : {
            "os_auth_url": "https://openstack.tacc.chameleoncloud.org:5000/v2.0"
        }
    }

    for site_name in sites_dict:
        site = Site()
        site.name = site_name
        site.os_auth_url = sites_dict[site_name]["os_auth_url"]
        site.save()

    print('This should not be called!')
