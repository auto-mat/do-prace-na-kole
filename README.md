
Skript na vytvoení anonimizovaných tras z DPNK

1. ssh into aws instance
2. do `sudo docker ps` to find a container to connect to
3. Run `sudo docker exec -it ubuntu_dpnk-worker_1 bash` to enter container
4. Run `apt-get install postgresql-client` in container to get postgres cli
5. ssh into another aws instance and run `cat secrets/docker.env` to find DB host and password
6. In the first instance run `wget https://raw.githubusercontent.com/timthelion/dpnk-tracks/master/refresh_views.sql` to get sql script from this repo.
7. Then run the script with `psql -h <DPNK_DB_HOST> -U dpnk -d dpnk_2017 -a -f refresh_views.sql` filling in DPNK_DB_HOST from the docker.env file. You will be asked for a DB password which you will also find in the docker.env file.
8. Now go to the [geoserver web interface](https://geoserver.prahounakole.cz/geoserver/web/)
9. Now select dpnk:dpnk-amazon
![](screenshots/screenshot_1.png)
10. Click the "Configure new SQL view..." link
![](screenshots/screenshot_2.png)
11. Configure the name for your new layer and set sql command making sure you have the right campaing_id. You should also check the "Guess geometry type and srid" checkbox.
![](screenshots/screenshot_3.png)
12. On the "Data" tab you need to select "EPSG:4326" as the SRS and click the "Compute from Data" links for the bounds.
![](screenshots/screenshot_4.png)
13. Finally, on the "Publishing" tab select "dpnk:gpxtrack" as the default style.
![](screenshots/screenshot_5.png)
14. The last step is updating [the code](https://github.com/auto-mat/prahounakole/blob/master/apps/cyklomapa/static/js/mapa.js) to include the new layer and publish the changes to the server.

