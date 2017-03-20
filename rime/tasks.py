import time
import traceback

from celery import shared_task
from celery.utils.log import get_task_logger
import requests

from resource_manager.celery import app
from . import models

logger = get_task_logger(__name__)


@shared_task
def monitor_cluster(cluster_id):
    logger.info('Starting monitoring of cluster {}'.format(cluster_id))
    cluster = models.Cluster.objects.get(id=cluster_id)
    logger.info('Cluster {} known state: "{}"'.format(cluster_id, cluster.remote_status))

    while True:
        logger.info('Polling remote state of cluster {}'.format(cluster_id))
        stack_data = cluster.get_stack()
        if stack_data.stack_status != cluster.remote_status:
            logger.info('Remote state of cluster {} transitioned from "{}" to "{}"'.format(
                cluster_id, cluster.remote_status, stack_data.stack_status))
            cluster.remote_status = stack_data.stack_status
            cluster.save()
            break

        time.sleep(5)


def outputs(stack):
    return {so['output_key']: so['output_value'] for so in stack.outputs}


@shared_task
def monitor_startup(cluster_id):
    logger.info('Monitoring startup of cluster {}'.format(cluster_id))
    cluster = models.Cluster.objects.get(id=cluster_id)

    while True:
        time.sleep(5)

        logger.info('Polling remote state of cluster {}'.format(cluster_id))
        stack = cluster.get_stack()
        if stack.action == 'CREATE':
            if stack.status == 'IN_PROGRESS':
                continue

            elif stack.status == 'FAILED':
                logger.warning('Remote cluster failed to start')
                cluster.status = 'ERROR'
                break

            elif stack.status == 'COMPLETE':
                logger.info('Remote cluster startup complete')
                outs = outputs(stack)
                try:
                    cluster.address = outs['master_ip']
                except KeyError:
                    logger.warning('Remote cluster didn\'t provide required output!')
                    cluster.status = 'ERROR'
                else:
                    cluster.status = 'READY'
                break

        else:
            logger.warning('Remote cluster action not in CREATE! (is "{}")'.format(stack.action))
            break

    cluster.remote_status = stack.stack_status
    cluster.save()


@shared_task
def monitor_startup_resource(resource_id):
    logger.info('Monitoring startup of resource {}'.format(resource_id))
    resource = models.Resource.objects.get(id=resource_id)
    cluster = resource.cluster

    while True:
        if cluster.status == 'READY':
            break
        time.sleep(1)
        cluster.refresh_from_db()

    service_url = 'http://{}:8012'.format(cluster.address)
    while True:
        try:
            response = requests.post(service_url + '/new_account/')
        except requests.exceptions.ConnectionError as e:
            logger.info('Couldn\'t connect to cluster {} on behalf of resource {}, retrying later.'.format(cluster.id, resource.id))
            time.sleep(5)
            continue
        else:
            account = response.json()
            break

    logger.info('Got new account for resource {}.'.format(resource.id))
    resource.username = account['username']
    resource.password = account['password']
    resource.save()
