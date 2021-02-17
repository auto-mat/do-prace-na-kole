from __future__ import absolute_import

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from django.conf import settings  # noqa

app = Celery("apps.dpnk")

app.conf.task_routes = (
    [
        ("stravasync.tasks.*", {"queue": "stravasync"}),
    ],
)

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
