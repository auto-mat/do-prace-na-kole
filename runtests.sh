#!/bin/bash -e
export DJANGO_SETTINGS_MODULE="project.test_settings"
coverage run ./runtests.py $@ --with-timer
coverage html
