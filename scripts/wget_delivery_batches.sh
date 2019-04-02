#!/bin/bash
./dpnk_login.sh || exit
curl --silent -b cookies.txt --referer "https://dpnk.dopracenakole.cz/admin/login/" --output out.html "https://dpnk.dopracenakole.cz/admin/t_shirt_delivery/deliverybatch/$1/change/" 
cat out.html | grep "https://dpnk.s3-eu-west-1.amazonaws.com:443/customer_sheets/customer_sheets_" | sed "s/.*href=\"//" | sed "s/\">.*//" | sed "s/\&amp;/\&/g" | wget -i - --directory-prefix=$2
