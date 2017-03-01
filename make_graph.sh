#!/bin/sh
env/bin/python manage.py graph_models dpnk --exclude-columns="created_by,updated_by,author"  --pydot  -g -o graph.pdf
