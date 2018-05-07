#!/bin/bash
if python manage.py showmigrations | grep '\[ \]\|^[a-z]' | grep '[  ]' -B 1; then
   python manage.py migrate --noinput                # Apply database migrations
   python manage.py denorm_drop
   python manage.py denorm_init
fi

# Prepare log files and start outputting logs to stdout
tail -n 0 -f logs/*.log &

service memcached restart

GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-"60"}

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn wsgi:application \
	 --name dpnk \
	 --bind 0.0.0.0:8000 \
	 --workers $GUNICORN_NUM_WORKERS \
	 --timeout $GUNICORN_TIMEOUT \
	 --log-level=debug \
	 --log-file=- \
	 --access-logfile=- \
	 "$@"
