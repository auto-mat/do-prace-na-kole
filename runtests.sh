#!/bin/bash
sudo /etc/init.d/memcached restart
DJANGO_SETTINGS_MODULE="project.test_settings" env/bin/coverage run ./runtests.py $@ --with-timer && env/bin/coverage html
