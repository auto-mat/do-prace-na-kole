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

Building the docker images
--------------------------

    $ make docker-compose

Launching the docker-compose containers
---------------------------------------

    $ sudo docker-compose -f docker-compose-dev.yml up

Setting up the database
---------------------

    $ sudo docker exec -it dopracenakole_web_1 bash

    # su test
    $ ./setup.sh
    $ python3 manage.py createsuperuser

Launching the development webserver
------------------------------------

In one window launch the livereload server

    $ sudo docker exec -it dopracenakole_web_1 bash
    $ python manage.py livereload --host 0.0.0.0
    
And in another window launch the development webserver

    $ sudo docker exec -it dopracenakole_web_1 bash
    $ python3 manage.py runserver 0.0.0.0:8021
    


Setting up the server for the first time
----------------------------------------

On your first visit you should go to the URL:

Go to <http://test.localhost:8021/admin/dpnk/campaign/>

Log in.

Add a campaign named Test and individual phases.

Add a user profile for your user <http://test.localhost:8021/admin/dpnk/userprofile/>

Now you can go to 'http://test.localhost:8021/' and start to play around.

Backing up your database
------------------------

Once you have your test environment working, it's a good idea to back up your database.

First stop docker compose

    $ docker-compose -f docker-compose-dev.yml down

Then copy db folder

    $ cp -r ./db ./db-bk

