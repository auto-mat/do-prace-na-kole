
Skript na vytvoení anonimizovaných tras z DPNK

1. ssh into aws instance
2. do `sudo docker ps` to find a container to connect to
3. Run `sudo docker exec -it ubuntu_dpnk-worker_1 bash` to enter container
4. Run `apt-get install postgresql-client` in container to get postgres cli
5. ssh into another aws instance and run `cat secrets/docker.env` to find DB host and password
6. In the first instance run `wget https://raw.githubusercontent.com/timthelion/dpnk-tracks/master/refresh_views.sql` to get sql script from this repo.
7. Then run the script with `psql -h <DPNK_DB_HOST> -U dpnk -d dpnk_2017 -a -f refresh_views.sql` filling in DPNK_DB_HOST from the docker.env file. You will be asked for a DB password which you will also find in the docker.env file.

