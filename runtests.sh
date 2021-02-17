#!/bin/bash -e
export DJANGO_SETTINGS_MODULE="project.settings.test"
DB=admin-smoke-test python ./runtests.py dpnk.test.test_admin_smoke --with-timer & p1=$! # https://stackoverflow.com/a/9258753/2126889
DB=dpnk-test coverage run ./runtests.py dpnk $@ --with-timer --exclude-test=dpnk.test.test_admin_smoke.AdminSmokeTests --exclude-test=dpnk.test.test_admin --exclude-test=dpnk.test.test_views --exclude-test=dpnk.test.test_email & p2=$!
DB=dpnk-admin-test coverage run ./runtests.py dpnk.test.test_admin $@ --with-timer & p3=$!
DB=dpnk-email-test coverage run ./runtests.py dpnk.test.test_email $@ --with-timer & p4=$!
DB=dpnk-views-test coverage run ./runtests.py dpnk.test.test_views $@ --with-timer & p5=$!
DB=coupons-test coverage run ./runtests.py coupons $@ --with-timer & p6=$!
DB=donation_chooser-test coverage run ./runtests.py donation_chooser $@ --with-timer  & p7=$!
DB=psc-test coverage run ./runtests.py psc $@ --with-timer & p8=$!
DB=motivation_messages-test coverage run ./runtests.py motivation_messages $@ --with-timer & p9=$!
DB=stale_notifications-test coverage run ./runtests.py stale_notificaitons $@ --with-timer & p10=$!
DB=stravasync-test coverage run ./runtests.py stravasync $@ --with-timer & p11=$!
DB=t_shirt_delivery-test coverage run ./runtests.py t_shirt_delivery $@ --with-timer & p12=$!
wait $p1 &&
wait $p2 &&
wait $p3 &&
wait $p4 &&
wait $p5 &&
wait $p6 &&
wait $p7 &&
wait $p8 &&
wait $p9 &&
wait $p10 &&
wait $p11 &&
wait $p12 &&
coverage html
