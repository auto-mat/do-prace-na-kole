#!/bin/bash

# run Celery worker for our project myproject with Celery configuration stored in Celeryconf
echo Starting celery worker
celery worker -A project.celery -l info --queues ${CELERY_TASK_QUEUES:-celery} --hostname ${CELERY_HOSTNAME:-dpnk-worker}
