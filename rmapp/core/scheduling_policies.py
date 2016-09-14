from rmapp.models import Credential
import json

class AbstractSchedulingPolicy(object):

    def choose_appliance_implementation(self, appliances, implementations, sites, clusters):
        raise not NotImplemented


class SimpleSchedulingPolicy(AbstractSchedulingPolicy):

    def choose_appliance_implementation(self, appliance, implementations, sites, clusters, hints=None):
        """ This function should return a 3-uplet (appliance_impl, common_applaince_impl, credential)"""
        asked_sites = []
        # HINT INSERTION: Add a hint to this function to help to chose the right site
        all_credentials = list(Credential.objects.all())
        if hints is not None:
            requested_credentials = json.loads(hints)["credentials"]
            all_credentials = filter(lambda cred: cred.name in requested_credentials, all_credentials)

        appliance_implementations = filter(lambda i: i.appliance == appliance.name, implementations)
        if len(asked_sites) > 0:
            appliance_implementations = filter(lambda ai: ai.site in asked_sites, appliance_implementations)
        if len(appliance_implementations) > 0:
            for appliance_impl in appliance_implementations:
                common_appliances = filter(lambda i: i.appliance == "common", implementations)
                common_appliance_impl = common_appliances[0] if len(common_appliances) > 0 else None
                if not common_appliance_impl:
                    raise Exception("There was an issue while fetching the common appliance linked with this implementation %s", appliance_impl.name)
                credential_candidates = filter(lambda cred: cred.site_name == appliance_impl.site, all_credentials)
                matching_credential = credential_candidates[0] if len(credential_candidates) > 0 else None
                if credential_candidates:
                    return (appliance_impl, common_appliance_impl, matching_credential)
            raise Exception("Cannot find credentials for this appliance %s and these hints (%s)" % (appliance, hints))
        raise Exception("There was an issue while finding an accurate appliance %s with these hints (%s)" % (appliance, hints))
