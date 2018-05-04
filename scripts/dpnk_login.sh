#!/bin/bash
# Log in to DPNK and save it into session in cookies.txt
http_code=`curl --silent  --write-out %{http_code} "https://dpnk.dopracenakole.cz/admin/" --output /dev/null -c cookies.txt -b cookies.txt`
if [ $http_code -ne 200 ]; then
   curl --silent "https://dpnk.dopracenakole.cz/admin/login/" --output /dev/null -c cookies.txt -b cookies.txt
   read -p 'Enter username: ' username
   read -sp 'Enter password: ' password
   csrftoken=`grep csrftoken cookies.txt | cut -f 7`
   http_code=`curl --write-out %{http_code} --silent "https://dpnk.dopracenakole.cz/admin/login/" --referer "https://dpnk.dopracenakole.cz/admin/login/" --output /dev/null  -c cookies.txt -b cookies.txt -d "username=$username" -d "password=$password" -d "csrfmiddlewaretoken=$csrftoken"`
   [ $http_code -ne 302 ] && echo -e "\nWrong authentication" && exit 1
fi
echo "Successfully logged into DPNK"
