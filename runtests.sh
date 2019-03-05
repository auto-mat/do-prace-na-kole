#!/bin/bash -e
export DJANGO_SETTINGS_MODULE="project.settings.test"
coverage run ./runtests.py $@ --with-timer --exclude-test=dpnk.test.test_admin_smoke.AdminSmokeTests
python ./runtests.py dpnk.test.test_admin_smoke --with-timer
coverage html
