#!/bin/bash

curl "http://online.gls-czech.com/login.php" -c cookies.txt -b cookies.txt | grep script

if [ $? -ne 0 ] && [ -z "$username" ];  then
   read -sp 'Enter password: ' password
   echo -e "\n"
   read -p 'Enter username: ' username
   echo -e "\n"
fi

dateFrom="01.01.2019"
dateTo=`date +%d.%m.%Y`

curl "http://online.gls-czech.com/login.php" -d "username=$username" -d "password=$password" -d "lessersecurity=on"  -c cookies.txt -b cookies.txt

file=`curl "http://online.gls-czech.com/ll_getReportClass.php?uid=10424&lng=cz&fileType=CSV&dateFrom=$dateFrom&dateTo=$dateTo&senderID=-1&replist=0-30&gapid=-1" -c cookies.txt -b cookies.txt`
echo $file
echo "carrier_identification,id,dispatched" > dispatched_subsidiary_boxes.csv
curl "http://online.gls-czech.com/$file" -c cookies.txt -b cookies.txt > gls_data.csv
tail gls_data.csv -n+2 | tr -d '\r' | sed 's/"//g' | cut -d ";" -f 1,3,5 | sed 's/;[^;][^;]*$/;1/' | tr ";" , >> dispatched_subsidiary_boxes.csv
grep -P ",1\$|carrier" > dispatched_subsidiary_boxes_only_dispatched.csv < dispatched_subsidiary_boxes.csv
