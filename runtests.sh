#!/bin/bash
export DJANGO_SETTINGS_MODULE="project.test_settings"
env/bin/coverage run ./runtests.py $@ --with-timer && env/bin/coverage html
