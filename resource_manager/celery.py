import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resource_manager.settings')

app = Celery('resource_manager')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


# @app.on_after_configure.connect
# def setup_tasks(sender, **kwargs):
#     pass#sender.add_periodic_task(10.0, periodic_task.s(), name='add every 10')

#
# @app.task(bind=True)
# def periodic_task(self):
#     # print("Calling check_operations_periodically task")
#     check_operations_periodically()
