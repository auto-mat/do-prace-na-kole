#!/bin/sh

# run Celery worker for our project myproject with Celery configuration stored in Celeryconf
echo Starting celery worker
celery worker -A project.celery
