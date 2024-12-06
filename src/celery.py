# my_proj/my_proj/celery.py
from __future__ import absolute_import

import os
import ssl

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')
 

app = Celery('src',
     broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
     },
     redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE
     })
 

app.config_from_object('django.conf:settings', namespace='CELERY')
# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.update(
    worker_cancel_long_running_tasks_on_connection_loss=False,
)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')