#!/bin/bash
sudo /etc/init.d/memcached restart
DJANGO_SETTINGS_MODULE="project.settings" env/bin/coverage run ./runtests.py $@ --with-timer
DJANGO_SETTINGS_MODULE="project.settings" env/bin/coverage html
