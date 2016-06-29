
if __name__ == "__main__":
    from django.conf import settings
    if not settings.configured:
        settings.configure(DEBUG=True)

    from webservice.models import Cluster



    if len(Cluster.objects.all()) == 0:
        mock_clusters = [
            {"name": "hadoop", "site": "KVM@TACC"},
            {"name": "hadoop2", "site": "KVM@TACC"},
            {"name": "mongodb1", "site": "KVM@TACC"},
        ]

        for mock_cluster in mock_clusters:
            new_cluster = Cluster()
            new_cluster.name = mock_cluster["name"]
            new_cluster.site = mock_cluster["site"]
            new_cluster.save()