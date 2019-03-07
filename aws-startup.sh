#!/bin/sh
POSTFIX=$(cat postfix)
git clone https://git-codecommit.eu-west-1.amazonaws.com/v1/repos/do-prace-na-kole-secrets$POSTFIX secrets
cp secrets/docker.env docker.env
if [ "${POSTFIX}" == "-test" ]; then
    BRANCH="devel"
elif  [ "${POSTFIX}" == "-prod" ]; then
    BRANCH="master"
fi
wget 'https://raw.githubusercontent.com/auto-mat/do-prace-na-kole/$BRANCH/docker-compose.yml'
wget 'https://raw.githubusercontent.com/auto-mat/do-prace-na-kole/$BRANCH/restart_docker_server'
chmod +x restart_docker_server
sh restart_docker_server
