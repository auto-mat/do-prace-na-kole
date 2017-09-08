#!/bin/bash -e
export DJANGO_SETTINGS_MODULE="project.test_settings"
coverage run ./runtests.py $@ --with-timer --exclude-test=dpnk.test.test_admin_smoke.AdminSmokeTests
python ./runtests.py dpnk.test.test_admin_smoke --with-timer
coverage html
