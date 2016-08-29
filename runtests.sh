#!/bin/bash -e
export DJANGO_SETTINGS_MODULE="project.test_settings"
source env/bin/activate
flake8
env/bin/coverage run ./runtests.py $@ --with-timer
env/bin/coverage html
