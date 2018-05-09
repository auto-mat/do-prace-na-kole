#!/bin/bash
read -sp 'Enter password: ' password
echo -e "\n"
username="050013079"
dateFrom="1.04.2018"
dateTo="20.06.2018"
if [ -z ${sessionID} ]; then
   read -p 'Enter session ID: ' sessionID
   echo -e "\n"
fi
file=`curl 'http://online.gls-czech.com/ll_getReportClass.php?uid=10424&lng=cz&fileType=CSV&dateFrom=1.04.2018&dateTo=30.04.2018&senderID=-1&replist=0-30&gapid=-1' -H "Cookie: PHPSESSID=$sessionID; SRV_ID=01; cookie[userdata][lessersecurity]=1; cookie[userdata][username]=$username; cookie[userdata][password]=$password"`
echo $file
echo "carrier_identification,id,dispatched" > dispatched_subsidiary_boxes.csv
curl "http://online.gls-czech.com/$file" -H "Cookie: PHPSESSID=$sessionID; SRV_ID=01; cookie[userdata][lessersecurity]=1; cookie[userdata][username]=$username; cookie[userdata][password]=$password" > gls_data.csv
cat gls_data.csv | tr -d '\r' | sed 's/"//g' | cut -d ";" -f 1,3,5 | grep -P ';..*;' | sed 's/;[^;][^;]*$/;1/' | tr ";" , >> dispatched_subsidiary_boxes.csv
grep -P ",1\$|carrier" > dispatched_subsidiary_boxes_only_dispatched.csv < dispatched_subsidiary_boxes.csv
