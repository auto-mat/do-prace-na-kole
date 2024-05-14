#!/usr/bin/env bash

if poetry run python manage.py showmigrations | grep '\[ \]\|^[a-z]' | grep '[  ]' -B 1; then
   poetry run python manage.py migrate --noinput                # Apply database migrations
   poetry run python manage.py update_translation_fields
   poetry run python manage.py denorm_drop
   poetry run python manage.py denorm_init
fi

# Prepare log files and start outputting logs to stdout
tail -n 0 -f logs/*.log &

service memcached restart

# Start Gunicorn processes
echo Starting Gunicorn.
exec poetry run gunicorn wsgi:application \
	 --name dpnk \
	 --bind 0.0.0.0:${GUNICORN_PORT:-"8000"} \
	 --workers ${GUNICORN_NUM_WORKERS:-"6"} \
	 --threads ${GUNICORN_NUM_THREADS:-"2"} \
	 --timeout ${GUNICORN_TIMEOUT:-"60"} \
	 --preload \
	 --log-level=debug \
	 --log-file=- \
	 --access-logfile=- \
	 "$@"
