import time
import traceback

from celery import shared_task
from celery.utils.log import get_task_logger

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

#
# @shared_task
# def check_operations_periodically():
#     # print("checking executions")
#     executions = Execution.objects.filter(ongoing_transition=False)
#     exections = [e for e in executions if e.operation_state not in ["error", "finished"]]
#     if executions:
#         process_execution_state.delay(execution.id)
#
#
# @shared_task
# def process_execution_state(execution_pk):
#     execution = Execution.objects.get(id=execution_pk)
#     state_info = execution.get_operation_state_info()
#
#     possible_transitions = [t for t in state_info.possible_transitions if t.to_state != 'error']
#
#     # print("Execution '{}' is in state '{}', can go to {}".format(
#     #     execution_pk, execution.operation_state,
#     #     [t.get_name() for t in possible_transitions],
#     # ))
#
#     try:
#         if len(possible_transitions) > 0:
#             # # Make a transition
#             # chosen_transition = possible_transitions[0]
#             # print("Commanding transition of execution '{}' to '{}'".format(
#             #     execution_pk, chosen_transition.get_name(),
#             # ))
#             state_info.make_transition(chosen_transition.get_name(), user=execution.author)
#     except Exception as e:
#         print(traceback.format_exc())
#     finally:
#         execution.ongoing_transition = False
#         execution.save()
