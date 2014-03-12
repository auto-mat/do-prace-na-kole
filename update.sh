#!/bin/sh

git pull
env/bin/pip install -r requirements.txt
if [ "$1" = "migrate" ]; then
   echo "Backuping db..."
   mkdir db_backup
   env/bin/python manage.py dumpdata  --indent=4 --all -e south -e sessions -e contenttypes > sql/dpnk-`git rev-parse --short HEAD`-`date +"%y%m%d-%H:%M:%S"`.json
   echo "Migrating..."
   env/bin/python manage.py migrate
fi
env/bin/python manage.py collectstatic --noinput
touch wsgi.py
