#!/bin/sh

# run Celery worker for our project myproject with Celery configuration stored in Celeryconf
echo Starting celery beat
single-beat celery beat -A project.celery -S django -l info
