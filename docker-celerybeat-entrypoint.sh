#!/usr/bin/env bash

# run Celery worker for our project myproject with Celery configuration stored in Celeryconf
echo "Starting celery beat"
exec poetry run celery beat -A project.celery --scheduler django_celery_beat.schedulers:DatabaseScheduler --loglevel="${CELERY_BEAT_LOGLEVEL-info}"
