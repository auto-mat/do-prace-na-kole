#!/bin/bash
# Log in to DPNK and save it into session in cookies.txt
HOST_NAME=${HOST_NAME:-"dpnk.dopracenakole.cz"}
PROTOCOL=${PROTOCOL:-"https"}
PORT=${PORT:-"443"}
BASE_ADDRESS="$PROTOCOL://$HOST_NAME"
ADDRESS="$BASE_ADDRESS:$PORT"
echo connecting to $ADDRESS
http_code=`curl --silent  --write-out %{http_code} "$ADDRESS/aplikace/" --output /dev/null -c cookies.txt -b cookies.txt`
if [ $http_code = 000 ]; then
   echo "Site not reachable"
   exit 3
fi
if [ $http_code -ne 200 ]; then
   curl --silent "$ADDRESS/login/" --output output.html -c cookies.txt -b cookies.txt
   read -p 'Enter username: ' username
   read -sp 'Enter password: ' password
   echo -e "\n"
   csrftoken=`grep "$HOST_NAME.*csrftoken" cookies.txt | cut -f 7`
   http_code=`curl --write-out %{http_code} --silent "$ADDRESS/login/" --referer "$BASE_ADDRESS/login/" --output output.html  -c cookies.txt -b cookies.txt -d "username=$username" -d "password=$password" -d "csrfmiddlewaretoken=$csrftoken"`
   [ $http_code -ne 302 ] && echo -e "\nWrong authentication, returned code $http_code" && exit 1
fi
echo "Successfully logged into DPNK"
