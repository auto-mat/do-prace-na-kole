#!/usr/bin/env bash

AUTOSSH="autossh"

if poetry run python manage.py showmigrations | grep '\[ \]\|^[a-z]' | grep '[  ]' -B 1; then
   poetry run python manage.py migrate --noinput                # Apply database migrations
   poetry run python manage.py update_translation_fields
   poetry run python manage.py denorm_drop
   poetry run python manage.py denorm_init
fi

# Prepare log files and start outputting logs to stdout
tail -n 0 -f logs/*.log &

service memcached restart

# AWS Aurora PG RDS proxy SSH tunnel
if command -v "${AUTOSSH}" &> /dev/null && test -n "${AWS_AURORA_PG_RDS_DPNK_PROXY_REMOTE_HOST}";
then
    "${AUTOSSH}" -o ServerAliveInterval=20 \
                 -o StrictHostKeyChecking=accept-new \
                 -i /root/.ssh/aurora-rds-pg-dpnk-db-proxy.pem \
                 -M 0 \
                 -N \
                 -L "${AWS_AURORA_PG_RDS_DPNK_PROXY_LOCALHOST_PORT-5432}":"${AWS_AURORA_PG_RDS_DPNK_PROXY_REMOTE_HOST}":"${AWS_AURORA_PG_RDS_DPNK_PROXY_REMOTE_HOST_PORT-5432}" \
                 "${AWS_E2C_AURORA_PG_RDS_DPNK_PROXY_REMOTE_USERNAME_WITH_HOST}" &
fi

# Start Gunicorn processes
echo Starting Gunicorn.
exec poetry run gunicorn wsgi:application \
	 --name dpnk \
	 --bind 0.0.0.0:${GUNICORN_PORT:-"8000"} \
	 --workers ${GUNICORN_NUM_WORKERS:-"6"} \
	 --timeout ${GUNICORN_TIMEOUT:-"60"} \
	 --preload \
	 --log-level=debug \
	 --log-file=- \
	 --access-logfile=- \
	 "$@"
