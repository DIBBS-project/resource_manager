from django.core.management.base import BaseCommand, CommandError
import heatclient.exc as heat_exc

from rime.models import Cluster


class Command(BaseCommand):
    help = 'Commands deletion of cluster(s) to free up the OS resources'

    def add_arguments(self, parser):
        parser.add_argument('cluster_id', nargs='+', type=str,
            help='One or more cluster IDs. The special value "all" is available.')

    def handle(self, *args, **options):
        if 'all' in options['cluster_id']:
            clusters = Cluster.objects.all()
        else:
            clusters = []
            dont_exist = []
            for cid in options['cluster_id']:
                try:
                    clusters.append(Cluster.objects.get(id=cid))
                except Cluster.DoesNotExist:
                    dont_exist.append(cid)

            if dont_exist:
                raise CommandError('Cluster(s) {} do not exist'.format(', '.join(dont_exist)))

        for cluster in clusters:
            # don't call .delete on the queryset (e.g. from .all()) as
            # that'll bypass the model's delete method. see
            # http://stackoverflow.com/a/19007641/194586 for a way to
            # evolve past that
            try:
                cluster.delete()
            except heat_exc.HTTPException as e:
                self.stdout.write('Error on deleting cluster "{}": {}'.format(cluster.id, str(e)))
            else:
                self.stdout.write(self.style.SUCCESS('Deleted cluster "{}"'.format(cluster.id)))
