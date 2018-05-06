#!/bin/bash

function unsecure_cookies {
   sed "s/TRUE/FALSE/" cookies.txt -i
   sed "s/^#HttpOnly_//" cookies.txt -i
}

./dpnk_login.sh || exit

unsecure_cookies

EXTRAHEADER="X-Forwarded-Proto: https"
HOST_NAME=${HOST_NAME:-"dpnk.dopracenakole.cz"}
PORT=${PORT:-"443"}
RESOLVE_URL=${RESOLVE_URL:-"dpnk.dopracenakole.cz"}
RESOLVE_PORT=${RESOLVE_PORT:-"80"}

function call_dpnk {
    OUTPUT=output.html
    OUTPUT=/dev/null
    curl\
     --cookie cookies.txt\
     --cookie-jar cookies.txt\
     -o $OUTPUT\
     --resolve "$HOST_NAME:$RESOLVE_PORT:$RESOLVE_URL"\
     $2\
     "$HOST_NAME/$1"
}


while true; do
   call_dpnk
   sleep 1
done

exit
# DATE=2018-05-04
#
# call_dpnk ""
#
# unsecure_cookies
# export csrfmiddlewaretoken=`grep 'rides-form' -A 1 output.html | grep csrfmiddlewaretoken | sed "s/^.*value='//" | sed "s/'.*//"`
# echo $csrfmiddlewaretoken
#
# call_dpnk "" "-d\
# form-INITIAL_FORMS=4&\
# form-MIN_NUM_FORMS=0&\
# form-MAX_NUM_FORMS=1000&\
# form-0-commute_mode=by_foot&\
# form-0-distance=6.35&\
# form-0-direction=trip_to&\
# form-0-user_attendance=19140&\
# form-0-date=$DATE&\
# initial-form-0-date=$DATE&\
# form-0-id=2235353&\
# submit=Odeslat&\
# csrfmiddlewaretoken=$csrfmiddlewaretoken"
