#!/bin/bash -e
export DJANGO_SETTINGS_MODULE="project.settings.test"
python ./runtests.py dpnk.test.test_admin_smoke --with-timer
./runtests.py dpnk $@ --with-timer --exclude-test=dpnk.test.test_admin_smoke.AdminSmokeTests --exclude-test=dpnk.test.test_admin --exclude-test=dpnk.test.test_views --exclude-test=dpnk.test.test_email
./runtests.py dpnk.test.test_admin $@ --with-timer
./runtests.py dpnk.test.test_email $@ --with-timer
./runtests.py dpnk.test.test_views $@ --with-timer
./runtests.py coupons $@ --with-timer
./runtests.py donation_chooser $@ --with-timer
./runtests.py psc $@ --with-timer
./runtests.py motivation_messages $@ --with-timer
./runtests.py stale_notificaitons $@ --with-timer
./runtests.py stravasync $@ --with-timer
./runtests.py t_shirt_delivery $@ --with-timer
