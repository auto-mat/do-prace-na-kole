#!/bin/bash
if python manage.py showmigrations | grep '\[ \]\|^[a-z]' | grep '[  ]' -B 1; then
   python manage.py migrate --noinput                # Apply database migrations
   python manage.py update_translation_fields
   python manage.py denorm_drop
   python manage.py denorm_init
fi

# Prepare log files and start outputting logs to stdout
tail -n 0 -f logs/*.log &

service memcached restart

# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn wsgi:application \
	 --name dpnk \
	 --bind 0.0.0.0:${GUNICORN_PORT:-"80"} \
	 --workers ${GUNICORN_NUM_WORKERS:-"6"} \
	 --timeout ${GUNICORN_TIMEOUT:-"60"} \
	 --log-level=debug \
	 --log-file=- \
	 --access-logfile=- \
	 "$@"
