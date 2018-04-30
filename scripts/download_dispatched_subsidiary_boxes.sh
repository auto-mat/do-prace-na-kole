#!/bin/bash
read -sp 'Enter password: ' password
username="050013079"
dateFrom="1.04.2018"
dateTo="20.06.2018"
file=`curl "http://online.gls-czech.com/ll_getReportClass.php?uid=10424&lng=cz&fileType=CSV&dateFrom=$dateFrom&dateTo=$dateTo&senderID=-1&replist=0-30&gapid=-1" -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: cs,en;q=0.9,en-GB;q=0.8' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/65.0.3325.181 Chrome/65.0.3325.181 Safari/537.36' -H 'Accept: */*' -H 'Referer: http://online.gls-czech.com/ll_createreport.php' -H "Cookie: PHPSESSID=p085ci3bv4nbjb4vigqhh4lqd2; SRV_ID=01; cookie[userdata][lessersecurity]=1; cookie[userdata][username]=$username; cookie[userdata][password]=$password" -H 'Connection: keep-alive' --compressed`
echo "id,dispatched" > dispatched_subsidiary_boxes.csv
curl "http://online.gls-czech.com/$file" -H 'Accept-Encoding: gzip, deflate' -H 'Accept-Language: cs,en;q=0.9,en-GB;q=0.8' -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/65.0.3325.181 Chrome/65.0.3325.181 Safari/537.36' -H 'Accept: */*' -H 'Referer: http://online.gls-czech.com/ll_createreport.php' -H 'Cookie: PHPSESSID=p085ci3bv4nbjb4vigqhh4lqd2; SRV_ID=01; cookie[userdata][lessersecurity]=1; cookie[userdata][username]=050013079; cookie[userdata][password]=lavice107' -H 'Connection: keep-alive' --compressed | tr -d '\r' | sed 's/";"/\t/g' | sed 's/"//g' | cut -f 3,5 | grep -P '..*\t..*' | cut -f 1 | sed 's/$/,1/' | head -n -1 >> dispatched_subsidiary_boxes.csv

