def reset_data():
    pass


def create_infrastructure():
    from rpapp.models import Site, User, Cluster, Host
    # from conf.secret import secret
    # username = secret["username"]
    # password = secret["password"]
    # project = secret["project"]

    sites_dict = {
        "KVM@TACC" : {
            "os_auth_url": "https://openstack.tacc.chameleoncloud.org:5000/v2.0"
        }
    }
    # users_dict = {
    #     username: {
    #         "password": password,
    #         "project": project
    #     }
    # }
    softwares_dict = {
        "common": {
            "update_hosts_file": "templates/common/update_hosts_file.jinja2"
        },
        "hadoop": {
            "configure_node": "templates/hadoop/configure_node.jinja2",
            "prepare_node": "templates/hadoop/prepare_node.jinja2",
            "update_master_node": "templates/hadoop/update_master_node.jinja2",
            "user_data": "templates/hadoop/user_data.jinja2"
        },
        "mongodb": {
            "configure_node": "templates/mongodb/configure_node.jinja2",
            "prepare_node": "templates/mongodb/prepare_node.jinja2",
            "update_master_node": "mongodb/hadoop/update_master_node.jinja2",
            "user_data": "templates/mongodb/user_data.jinja2"
        }
    }

    events_names = []
    for software in softwares_dict:
        for event in softwares_dict[software]:
            if event not in events_names:
                events_names += [event]

    sites = []
    for site_name in sites_dict:
        site = Site()
        site.name = site_name
        site.os_auth_url = sites_dict[site_name]["os_auth_url"]
        site.save()
        sites += [site]

    print('This should not be called!')

    # users = []
    # for user_name in users_dict:
    #     user = UserProfile()
    #     user.username = user_name
    #     user.password = users_dict[user_name]["password"]
    #     user.project = users_dict[user_name]["project"]
    #     user.save()
    #     users += [user]

    # events = {}
    # for event_name in events_names:
    #     event = Event()
    #     event.name = event_name
    #     event.save()
    #     events[event_name] = event
    #
    # softwares = {}
    # for software_name in softwares_dict:
    #     software = Software()
    #     software.name = software_name
    #     software.save()
    #     softwares[software_name] = software
    #
    #     for event_name in softwares_dict[software_name]:
    #         script = Script()
    #         # script.code = softwares_dict[software_name][event_name]
    #         script.link_to_template = softwares_dict[software_name][event_name]
    #         script.software = software
    #         script.event = events[event_name]
    #         script.save()

    # clusters_names = ["hadoop_1", "hadoop_2", "hadoop_3"]
    # instance_count = 0
    # for site in sites:
    #     for user in users:
    #         for cluster_name in clusters_names:
    #             cluster = Cluster()
    #             cluster.name = cluster_name
    #             cluster.user = user
    #             cluster.site = site
    #             software_name = cluster.name.split("_")[0]
    #             cluster.software = softwares[software_name]
    #             cluster.save()
    #             is_master = True
    #             for host_name in hosts_names:
    #                 node = Host()
    #                 node.name = host_name
    #                 node.is_master = is_master
    #                 node.instance_id = "instance_%s" % (instance_count)
    #                 node.cluster = cluster
    #                 node.save()
    #                 is_master = False
    #                 instance_count += 1
