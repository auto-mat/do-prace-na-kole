#!/bin/bash -e
export DJANGO_SETTINGS_MODULE="project.test_settings"
flake8
coverage run ./runtests.py $@ --with-timer
coverage html
