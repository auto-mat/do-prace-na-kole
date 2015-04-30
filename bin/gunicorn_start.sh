#!/bin/bash
 
NAME="dpnk" # Name of the application
DJANGODIR=/home/aplikace/dpnk-2015/releases/current # Django project directory
SOCKFILE=/home/aplikace/dpnk-2015/releases/current/run/gunicorn.sock # we will communicte using this unix socket
USER=www-data # the user to run as
GROUP=www-data # the group to run as
NUM_WORKERS=6 # how many worker processes should Gunicorn spawn
TIMEOUT=20000
DJANGO_SETTINGS_MODULE=project.settings # which settings file should Django use
DJANGO_WSGI_MODULE=wsgi # WSGI module name
 
echo "Starting $NAME as `whoami`"
 
# Activate the virtual environment
cd $DJANGODIR
source env/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH
 
# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR
 
# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec env/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
--name $NAME \
--workers $NUM_WORKERS \
--user=$USER --group=$GROUP \
--bind=unix:$SOCKFILE \
--timeout=20000 \
--log-level=debug \
--log-file=-
