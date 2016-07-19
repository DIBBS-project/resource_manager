
class AbstractSchedulingPolicy(object):

    def choose_appliance_implementation(self, appliances, implementations, sites, clusters):
        raise not NotImplemented


class DummySchedulingPolicy(AbstractSchedulingPolicy):

    def choose_appliance_implementation(self, appliance, implementations, sites, clusters, hints=None):
        if hints is None:
            hints = []
        appliance_implementations = filter(lambda x: x.appliance == appliance.name, implementations)
        if len(appliance_implementations) > 0:
            appliance_impl = appliance_implementations[0]
            try:
                site = appliance_impl.site
                candidates = filter(lambda x: x.site==site and x.appliance=="common",
                                    implementations)
                common_appliance_impl = candidates[0]
            except:
                raise Exception("There was an issue while fetching the common appliance linked with this implementation %s", appliance_impl.name)
            return(appliance_impl, common_appliance_impl)
        raise Exception("There was an issue while fetching the common appliance %s" % (appliance, ))
