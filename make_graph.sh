#!/bin/sh
PYTHON=env/bin/python
if [ ! -f $PYTHON ]; then
    PYTHON=$(which python3)
fi
$PYTHON manage.py graph_models dpnk --exclude-columns="created_by,updated_by,author"  --pydot  -g -o graph.png
