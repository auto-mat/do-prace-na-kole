Do Prace na Kole (Ride to work by Bike) competion django app
------------------------------------------------------------

The DPNK django application was developed to power the [Do Práce na Kole](https://www.dopracenakole.cz) bike to work competition run by the non-profit [Auto*mat](https://www.auto-mat.cz/) organization in the Czech Republic. With some work, you can modify it to run your own bike to work competition in your home country.

This readme file is intended to document how to develop and deploy the code.

Do práce na kole is designed to use Python 3.4+ and Django 2.1

Dependencies
------------

 - Docker

Running the dev env
===================

Check out and setup repo
------------------------

    $ git clone https://bitbucket.org/pdlouhy/do-prace-na-kole.git
    $ cd do-prace-na-kole

Create a docker.env file
------------------------

    DPNK_SECRET_KEY=lkjkljfdseioj
    DPNK_DB_NAME=dpnk
    DPNK_DB_USER=dpnk
    DPNK_DB_PASSWORD=foobar
    DPNK_DB_HOST=postgres
    GUNICORN_NUM_WORKERS=1
    DPNK_ALLOWED_HOSTS=.localhost
    DPNK_DEBUG=True
    DPNK_SECURE_SSL_REDIRECT=False
    DPNK_CSRF_COOKIE_SECURE=False
    DPNK_SECURE_SSL_REDIRECT=False
    DPNK_SESSION_COOKIE_SECURE=False
    DPNK_SITE_ID=1
    DPNK_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
    STRAVA_CLIENT_ID=<some-id>
    STRAVA_CLIENT_SECRET=<some-secret>

Create `settings_local.py` by copying settings_local_sample_docker.py
-------------------------------------------------------------------

    $ cd project
    $ cp settings_local_sample_docker.py settings_local.py
    $ cd ..

Build the dev docker image
--------------------------

    $ sudo docker build . -f DockerfileDev -t dpnk-test

Setup and launch postgis
------------------------

    $ sudo docker volume create dpnk-pgdata
    $ sudo docker run -v dpnk-pgdata:/var/lib/postgresql/data --hostname dpnk-postgres --name dpnk-postgres -e POSTGRES_PASSWORD=foobar -e POSTGRES_USER=dpnk -e PGDATA=/var/lib/postgresql/data/pgdata mdillon/postgis:9.6

Relaunching the container:

    $ ./postgres-container

Note: By using multiple container names you can have multiple postgres containers and dbs and switch between the dbs for testing purposes. Perhaps have one db per git branch.

Launching rabbitmq
-----------------

    $ ./rabbit-container

Launching celery
----------------
    $ ./celery_container

TODO: Add celery beat instructions

Launching dpnk server
---------------------

    $ ./dpnk_container

    $ # The first time you launch you need to do migrations and load some fixtures, get static files ect...
    $ su test

    $ bower install
    $ python3 manage.py collectstatic
    $ python3 manage.py migrate
    $ python3 manage.py createsuperuser
    $ python3 manage.py loaddata dpnk/fixtures/commute_mode.json
    $ python3 manage.py loaddata dpnk/fixtures/sitetree.json
    $ python3 manage.py loaddata dpnk/fixtures/sites.json
    $ python3 manage.py import_czech_psc
    $ python3 manage.py loaddata dpnk/fixtures/occupation.json

    $ # Once the fixtures have been loaded once, you only need to run the server.
    $ python3 manage.py runserver 0.0.0.0:8000

Setting up the server for the first time
----------------------------------------

On your first visit you should go to the URL:

Go to <http://test.localhost:8000/admin/dpnk/campaign/>

Log in.

Add a campaign named Test and individual phases.

Add a user profile for your user <http://test.localhost:8000/admin/dpnk/userprofile/>

Now you can go to 'http://test.localhost:8000/' and start to play around.

Backing up your database
------------------------

Once you have your test environment working, it's a good idea to back up your database.

First stop postgres

    $ docker stop dpnk-postgres

Then export the db

    $ docker run --volumes-from dpnk-postgres busybox tar -cO /var/lib/postgresql/data | gzip -c > sql/dpnk-db-template.tgz

You can reset your database to the "good" version by running

    $  docker run --rm --volumes-from dpnk-postgres busybox rm -rf /var/lib/postgresql/data/pgdata
    $  docker run --rm --volumes-from dpnk-postgres -v $(pwd)/sql:/backup busybox tar xvf /backup/dpnk-db-template.tgz var/lib/postgresql/data/pgdata

