#!/bin/bash -e
export DJANGO_SETTINGS_MODULE="project.settings.test"
coverage run ./runtests.py apps $@ --with-timer --exclude-test=apps.dpnk.test.test_admin_smoke.AdminSmokeTests
python ./runtests.py apps.dpnk.test.test_admin_smoke --with-timer
coverage html
