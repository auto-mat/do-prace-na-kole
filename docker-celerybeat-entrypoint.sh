#!/bin/sh

# run Celery worker for our project myproject with Celery configuration stored in Celeryconf
echo Starting celery beat
celery beat -A project.celery -S django
