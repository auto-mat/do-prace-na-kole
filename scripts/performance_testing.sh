#!/bin/sh

# export HOST_URL="http://test2017.dopracenakole.cz/cs"
# export USERNAME=test
# export PASSWORD=testtest1
rm cookies.txt

export HOST_URL="http://dpnk.localhost:8000/cs"
export USERNAME=pdlouhy
export PASSWORD=Tukam1

curl\
 -v\
 -c cookies.txt\
 -b cookies.txt\
 "$HOST_URL/login"

export CSRFTOKEN=`grep csrftoken cookies.txt | sed "s/.*\t//g"`

curl\
 -v\
 -c cookies.txt\
 -b cookies.txt\
 -d "\
username=$USERNAME&\
password=$PASSWORD&\
submit=Přihlásit&\
csrfmiddlewaretoken=$CSRFTOKEN"\
 "$HOST_URL/login"

curl\
 -v\
 -c cookies.txt\
 -b cookies.txt\
 "$HOST_URL/"

# while true; do
#    curl\
#     -v\
#     -c cookies.txt\
#     -b cookies.txt\
#     "$HOST_URL/" &
#    sleep 0.5
# done

# $DATE=2017-23-02
# 
# curl\
#  -v\
#  -c cookies.txt\
#  -b cookies.txt\
#  -d "\
# form-INITIAL_FORMS=1&\
# form-MIN_NUM_FORMS=0&\
# form-MAX_NUM_FORMS=1000&\
# form-0-commute_mode=by_foot&\
# form-0-distance=6.35&\
# form-0-direction=trip_to&\
# form-0-user_attendance=19140&\
# form-0-date=$DATE&\
# initial-form-0-date=$DATE&\
# form-0-id=1036223&\
# submit=Odeslat&\
# username=test&\
# password=testtest1&\
# csrfmiddlewaretoken=$CSRFTOKEN"\
#  "$HOST_URL/"

# curl 'http://test2017.dopracenakole.cz/' \
# -H 'Cookie: qtrans_front_language=cz; csrftoken=NUW14PxZdtV3E76tLJvrYEpfmyEcaqh8; sessionid=yti701yk3abk7kz1y25whvjyczfpjmrr; _ga=GA1.2.504921721.1453816377; __utmt=1; __utma=261934344.504921721.1453816377.1462101734.1462107395.53; __utmb=261934344.9.10.1462107395; __utmc=261934344; __utmz=261934344.1454066220.1.1.utmcsr=redirects|utmccn=301_Redirects|utmcmd=dpnk2015.dopracenakole.net' \
# -H 'Origin: http://test2017.dopracenakole.cz' \
# -H 'Accept-Encoding: gzip, deflate, lzma' \
# -H 'Accept-Language: cs-CZ,cs;q=0.8' \
# -H 'Upgrade-Insecure-Requests: 1' \
# -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36 OPR/36.0.2130.65' \
# -H 'Content-Type: application/x-www-form-urlencoded' \
# -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' \
# -H 'Cache-Control: max-age=0' \
# -H 'Referer: http://test2017.dopracenakole.cz/' \
# -H 'Connection: keep-alive' \
# --data 'form-TOTAL_FORMS=1\
# &form-INITIAL_FORMS=1\
# &form-MIN_NUM_FORMS=0\
# &form-MAX_NUM_FORMS=1000\
# &csrfmiddlewaretoken=8SS3FKP6P4XETY5KFmIlFQ66eLCjXGGO\
# &form-0-commute_mode=by_foot\
# &form-0-distance=6.35\
# &form-0-direction=trip_to\
# &form-0-user_attendance=19140\
# &form-0-date=2016-05-01\
# &initial-form-0-date=2016-05-01\
# &form-0-id=1036223\
# &submit=Odeslat' \
# --compressed
# 
# # curl 'http://test2017.dopracenakole.cz/' \
# # -H 'Accept-Encoding: gzip, deflate, lzma, sdch' \
# # -H 'Accept-Language: cs-CZ,cs;q=0.8' \
# # -H 'Upgrade-Insecure-Requests: 1' \
# # -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36 OPR/36.0.2130.65' \
# # -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' \
# # -H 'Referer: http://test2017.dopracenakole.cz/' \
# # -H 'Cookie: qtrans_front_language=cz; csrftoken=NUW14PxZdtV3E76tLJvrYEpfmyEcaqh8; sessionid=yti701yk3abk7kz1y25whvjyczfpjmrr; _ga=GA1.2.504921721.1453816377; __utmt=1; __utma=261934344.504921721.1453816377.1462101734.1462107395.53; __utmb=261934344.3.10.1462107395; __utmc=261934344; __utmz=261934344.1454066220.1.1.utmcsr=redirects|utmccn=301_Redirects|utmcmd=dpnk2015.dopracenakole.net' \
# # -H 'Connection: keep-alive' \
# # -H 'Cache-Control: max-age=0' \
# # --compressed
# # 
# # curl 'http://test2017.dopracenakole.cz/' \
# # -H 'Cookie: qtrans_front_language=cz; csrftoken=NUW14PxZdtV3E76tLJvrYEpfmyEcaqh8; sessionid=yti701yk3abk7kz1y25whvjyczfpjmrr; _ga=GA1.2.504921721.1453816377; __utmt=1; __utma=261934344.504921721.1453816377.1462101734.1462107395.53; __utmb=261934344.13.10.1462107395; __utmc=261934344; __utmz=261934344.1454066220.1.1.utmcsr=redirects|utmccn=301_Redirects|utmcmd=dpnk2015.dopracenakole.net' \
# # -H 'Origin: http://test2017.dopracenakole.cz' \
# # -H 'Accept-Encoding: gzip, deflate, lzma' \
# # -H 'Accept-Language: cs-CZ,cs;q=0.8' \
# # -H 'Upgrade-Insecure-Requests: 1' \
# # -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36 OPR/36.0.2130.65' \
# # -H 'Content-Type: application/x-www-form-urlencoded' \
# # -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' \
# # -H 'Cache-Control: max-age=0' \
# # -H 'Referer: http://test2017.dopracenakole.cz/' \
# # -H 'Connection: keep-alive' \
# # --data 'form-TOTAL_FORMS=10&form-INITIAL_FORMS=10&form-MIN_NUM_FORMS=0&form-MAX_NUM_FORMS=1000&csrfmiddlewaretoken=fR93fEheRVVjLXY8vJpezXFK6wRRO1kQ&form-0-commute_mode=no_work&form-0-distance=6.35&form-0-direction=trip_to&form-0-user_attendance=19140&form-0-date=2016-05-01&initial-form-0-date=2016-05-01&form-0-id=1036223&csrfmiddlewaretoken=fR93fEheRVVjLXY8vJpezXFK6wRRO1kQ&form-1-commute_mode=by_other_vehicle&form-1-distance=6.35&form-1-direction=trip_from&form-1-user_attendance=19140&form-1-date=2016-05-01&initial-form-1-date=2016-05-01&form-1-id=1036224&csrfmiddlewaretoken=fR93fEheRVVjLXY8vJpezXFK6wRRO1kQ&form-2-commute_mode=no_work&form-2-distance=6.35&form-2-direction=trip_to&form-2-user_attendance=19140&form-2-date=2016-05-02&initial-form-2-date=2016-05-02&form-2-id=1036225&csrfmiddlewaretoken=fR93fEheRVVjLXY8vJpezXFK6wRRO1kQ&form-3-commute_mode=no_work&form-3-distance=6.35&form-3-direction=trip_from&form-3-user_attendance=19140&form-3-date=2016-05-02&initial-form-3-date=2016-05-02&form-3-id=1036226&csrfmiddlewaretoken=fR93fEheRVVjLXY8vJpezXFK6wRRO1kQ&form-4-commute_mode=no_work&form-4-distance=6.35&form-4-direction=trip_to&form-4-user_attendance=19140&form-4-date=2016-05-03&initial-form-4-date=2016-05-03&form-4-id=1036220&csrfmiddlewaretoken=fR93fEheRVVjLXY8vJpezXFK6wRRO1kQ&form-5-commute_mode=no_work&form-5-distance=6.35&form-5-direction=trip_from&form-5-user_attendance=19140&form-5-date=2016-05-03&initial-form-5-date=2016-05-03&form-5-id=1036227&csrfmiddlewaretoken=fR93fEheRVVjLXY8vJpezXFK6wRRO1kQ&form-6-commute_mode=bicycle&form-6-distance=6.35&form-6-direction=trip_to&form-6-user_attendance=19140&form-6-date=2016-05-04&initial-form-6-date=2016-05-04&form-6-id=1036217&csrfmiddlewaretoken=fR93fEheRVVjLXY8vJpezXFK6wRRO1kQ&form-7-commute_mode=bicycle&form-7-distance=6.35&form-7-direction=trip_from&form-7-user_attendance=19140&form-7-date=2016-05-04&initial-form-7-date=2016-05-04&form-7-id=1036218&csrfmiddlewaretoken=fR93fEheRVVjLXY8vJpezXFK6wRRO1kQ&form-8-commute_mode=no_work&form-8-distance=6.35&form-8-direction=trip_to&form-8-user_attendance=19140&form-8-date=2016-05-05&initial-form-8-date=2016-05-05&form-8-id=1036219&csrfmiddlewaretoken=fR93fEheRVVjLXY8vJpezXFK6wRRO1kQ&form-9-commute_mode=bicycle&form-9-distance=6.35&form-9-direction=trip_from&form-9-user_attendance=19140&form-9-date=2016-05-05&initial-form-9-date=2016-05-05&form-9-id=1036216&submit=Odeslat' \
# # --compressed
# # 
# # curl 'http://test2017.dopracenakole.cz/' \
# # -H 'Accept-Encoding: gzip, deflate, lzma, sdch' \
# # -H 'Accept-Language: cs-CZ,cs;q=0.8' \
# # -H 'Upgrade-Insecure-Requests: 1' \
# # -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36 OPR/36.0.2130.65' \
# # -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8' \
# # -H 'Referer: http://test2017.dopracenakole.cz/' \
# # -H 'Cookie: qtrans_front_language=cz; csrftoken=NUW14PxZdtV3E76tLJvrYEpfmyEcaqh8; sessionid=yti701yk3abk7kz1y25whvjyczfpjmrr; _ga=GA1.2.504921721.1453816377; __utmt=1; __utma=261934344.504921721.1453816377.1462101734.1462107395.53; __utmb=261934344.3.10.1462107395; __utmc=261934344; __utmz=261934344.1454066220.1.1.utmcsr=redirects|utmccn=301_Redirects|utmcmd=dpnk2015.dopracenakole.net' \
# # -H 'Connection: keep-alive' \
# # -H 'Cache-Control: max-age=0' \
# # --compressed
