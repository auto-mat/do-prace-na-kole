#!/bin/bash
python manage.py migrate                  # Apply database migrations

# Prepare log files and start outputting logs to stdout
touch logs/gunicorn.log
touch logs/access.log
tail -n 0 -f logs/*.log &

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn wsgi:application \
    --name dpnk \
    --bind 0.0.0.0:8000 \
    --workers $GUNICORN_NUM_WORKERS \
    --timeout 6000 \
    --log-level=debug \
    --log-file=/home/aplikace/logs/gunicorn.log \
    --access-logfile=/home/aplikace/logs/access.log \
    "$@"
