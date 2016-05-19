#!/bin/bash
 
NAME="dpnk flower" # Name of the application
DJANGODIR=`dirname $0`/.. # Django project directory
SOCKFILE=$DJANGODIR/run/gunicorn.sock # we will communicte using this unix socket
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

exec env/bin/celery -A project flower
