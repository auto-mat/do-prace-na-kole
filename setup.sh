#!/bin/bash
npm install
npm run build
python3 manage.py collectstatic
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py sitetree_resync_apps
python3 manage.py import_czech_psc
python3 manage.py loaddata apps/dpnk/fixtures/commute_mode.json
python3 manage.py loaddata apps/dpnk/fixtures/sites.json
python3 manage.py loaddata apps/dpnk/fixtures/occupation.json
django-admin compilemessages
