from __future__ import absolute_import, unicode_literals
import os
from django.conf import settings
from celery import Celery


app = Celery('base', broker_url=settings.BROKER_URL)

# USE WHEN PROJECT GROWS
app.config_from_object('django.conf:settings')
app.conf.broker_url = settings.BROKER_URL

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(settings.INSTALLED_APPS)

imports = ('base.receive.tasks', 'base.send.tasks',)

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))