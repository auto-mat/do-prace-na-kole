#!/bin/bash
docker-compose down
docker-compose up -d
exec docker exec -u test -it do-prace-na-kole_web_1 bash --init-file "/app-v/dev-entrypoint.sh"
