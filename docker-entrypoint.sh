#!/bin/bash
python manage.py migrate --noinput                # Apply database migrations
python manage.py denorm_drop
python manage.py denorm_init

# Prepare log files and start outputting logs to stdout
tail -n 0 -f logs/*.log &

service memcached restart

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn wsgi:application \
	 --name dpnk \
	 --bind 0.0.0.0:8000 \
	 --workers $GUNICORN_NUM_WORKERS \
	 --timeout 6000 \
	 --log-level=debug \
	 --log-file=- \
	 --access-logfile=- \
	 "$@"
