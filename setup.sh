#!/bin/bash
poetry install
poetry run python3 manage.py collectstatic
poetry run python3 manage.py migrate
poetry run python3 manage.py createsuperuser
poetry run python3 manage.py sitetree_resync_apps
poetry run python3 manage.py import_czech_psc
poetry run python3 manage.py loaddata apps/dpnk/fixtures/commute_mode.json
poetry run python3 manage.py loaddata apps/dpnk/fixtures/sites.json
poetry run python3 manage.py loaddata apps/dpnk/fixtures/occupation.json
poetry run django-admin compilemessages
