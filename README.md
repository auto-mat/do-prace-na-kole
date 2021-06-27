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

    $ git clone https://github.com/auto-mat/do-prace-na-kole.git
    $ cd do-prace-na-kole

Create a docker.env file
------------------------

    $ cp docker.env.sample docker.env
    $ $EDITOR docker.env
    
Building the docker images
--------------------------

    $ make docker-compose

Launching the docker-compose containers
---------------------------------------

    $ sudo docker-compose up
    
Setting up the database
---------------------

    $ sudo docker exec -it dopracenakole_web_1 bash

    # su test
    $ ./setup.sh

Launching the development webserver
------------------------------------

In another window launch the development webserver

    $ sudo docker exec -it dopracenakole_web_1 bash
    # su test
    $ poetry shell
    $ python3 manage.py runserver 0.0.0.0:8021
    
Clone and launch the front end server according to its own docs: https://github.com/auto-mat/do-prace-na-kole-frontend
    


Setting up the server for the first time
----------------------------------------

On your first visit you should go to the URL:

Go to <http://test.localhost:8021/admin/dpnk/campaign/>

Log in.

Add a campaign named Test and individual phases.

Add a user profile for your user <http://test.localhost:8021/admin/dpnk/userprofile/>

Now you can go to 'http://test.localhost:8021/' and start to play around.

Deployment
------------

Every time you push changes to github, new builds will be built. In this case, a build is a docker image. There are a number of scripts which you can find in the `scripts` directory of this repository. In order to deploy to test you need to first find the ip address of the test server

```
./scripts/sync-hosts.py
```

Then you can run

```
./scripts/restart_containers_on_server <ip-of-test-server>
```

This will update the test server to the latest build.

In order to deploy to production you should first deploy to test, then, after testing a bit, look at the build number on test. The build number can be found at the bottom of the menu. It is in a format like ` 2021.1212 . 2021.24 ` which stands for `<backend-build-number> . <frontend-build-number>`.

In order to deploy from test to production you will need to run the script.

```
./deploy_from_test_to_prod <backend-build-number>
```

Deploying [the frontend](https://github.com/auto-mat/do-prace-na-kole-frontend) is similar. There is a script.

```
./scripts/deploy_frontend --help
```

Which helps you deploy frontend builds. This script is documented. To see it's documentation simply run the script with the `--help` flag.

Backing up your database
------------------------

Once you have your test environment working, it's a good idea to back up your database.

First stop docker compose

    $ docker-compose down

Then copy db folder

    $ cp -r ./db ./db-bk

