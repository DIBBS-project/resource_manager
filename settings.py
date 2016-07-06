def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


@singleton
class Settings(object):

    def __init__(self):
        """
        Constructor
        """
        self.appliance_registry_url = "http://127.0.0.1:8003"
        self.process_registry_url = "http://127.0.0.1:8000"
        self.process_dispatcher_url = "http://127.0.0.1:8001"
        self.resource_provisioner_url = "http://127.0.0.1:8002"
