#!/usr/bin/env bash

# run Celery worker for our project myproject with Celery configuration stored in Celeryconf
echo "Starting celery worker"
exec poetry run celery worker -A project.celery --pool=prefork --concurrency="${CELERY_CONCURENCY-4}" --loglevel="${CELERY_LOGLEVEL-info}" --pidfile=/tmp/celery-beat.pid
