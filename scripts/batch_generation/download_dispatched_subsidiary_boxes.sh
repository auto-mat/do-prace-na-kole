#!/bin/bash

curl -X POST -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=$username&password=$password&lessersecurity=on" \
     -c cookies.txt \
     "$GLS_BASE_URL/login.php"

date_from=$GLS_DISPATCHED_SUBSIDIARY_BOXES_DATE_FROM
if [ "$GLS_DISPATCHED_SUBSIDIARY_BOXES_DATE_TO" == "date +%d.%m.%Y" ]; then
    date_to=$($GLS_DISPATCHED_SUBSIDIARY_BOXES_DATE_TO)
else
    date_to=${GLS_DISPATCHED_SUBSIDIARY_BOXES_DATE_TO-$(date +%d.%m.%Y)}
fi

file=$(curl -b cookies.txt "$GLS_BASE_URL/ll_getReportClass.php?uid=10424&lng=cz&fileType=CSV&dateFrom=$date_from&dateTo=$date_to&senderID=-1&replist=0-30&gapid=-1")
echo "carrier_identification,id,dispatched" > dispatched_subsidiary_boxes.csv
echo "$GLS_BASE_URL/$file"
curl -b cookies.txt -L "$GLS_BASE_URL/$file" > gls_data.csv
tail gls_data.csv -n+2 | tr -d '\r' | sed 's/"//g' | cut -d ";" -f 1,3,5 | sed 's/;[^;][^;]*$/;1/' | tr ";" , >> dispatched_subsidiary_boxes.csv
grep -P ",1\$|carrier" > dispatched_subsidiary_boxes_only_dispatched.csv < dispatched_subsidiary_boxes.csv
