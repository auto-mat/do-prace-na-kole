Do Prace na Kole (Ride to work by Bike) competion django app
------------------------------------------------------------

The DPNK django application was developed to power the [Do Práce na Kole](https://www.dopracenakole.cz) bike to work competition run by the non-profit [Auto*mat](https://www.auto-mat.cz/) organization in the Czech Republic. With some work, you can modify it to run your own bike to work competition in your home country.

This readme file is intended to document how to develop and deploy the code.

Do práce na kole is designed to use Python 3.4+ and Django 2.1

Dependencies
------------

 - Docker Engine
 - Docker Compose

Check [docker](https://docs.docker.com/) documentation for installation instructions

Setting up the dev env
===================

Click thumbnail for video instructions.

[![Alt text for your video](https://img.youtube.com/vi/7A8kPsMj5uE/0.jpg)](http://www.youtube.com/watch?v=7A8kPsMj5uE)

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

Setting up the database
---------------------

In a separate terminal window:

    $ sudo docker exec -it do-prace-na-kole_web_1 bash

    # su test
    $ ./setup.sh

Launching the development webserver
------------------------------------

    $ sudo docker exec -it dopracenakole_web_1 bash
    # su test
    $ poetry shell
    $ python3 manage.py runserver 0.0.0.0:8000
    
Clone and launch the front end server according to its own docs: https://github.com/auto-mat/do-prace-na-kole-frontend

Open the web app
-------------------

Go to `http://test.lvh.me:8021/`.

Backing up your local development database
---------------------------------------------------

Once you have your test environment working, it's a good idea to back up your database.

First stop docker compose

    $ docker-compose down

Then copy db folder

    $ cp -r ./db ./db-bk



Deployment
------------

Every time you push changes to github, new builds will be built. In this case, a build is a docker image. 

In order to deploy to production you should first deploy to test, then, after testing a bit, look at the build number on test. Deployment is done by updating build numbers in [the kubernetes config](https://github.com/auto-mat/k8s).  The build number can be found at the bottom of the menu. It is in a format like ` 2021.1212 . 2021.24 ` which stands for `<backend-build-number> . <frontend-build-number>`.

Deploying [the frontend](https://github.com/auto-mat/do-prace-na-kole-frontend) is similar. There is a script.

```
./scripts/deploy_frontend --help
```

Which helps you deploy frontend builds. This script is self documenting. To see it's documentation simply run the script with the `--help` flag.

Connecting to test and production servers (bash and python shell)
------------------------------------------------------------------------------

The `pyshell` script is quite usefull for this

```
./scripts/pyshell
```

For example, to get a python shell on the production instance run.

```
./scripts/pyshell dpnk --instance 0
```

To get a bash shell in the docker container run

```
./scripts/pyshell dpnk --instance 0 --cmd bash
```

And to get it directly on the host run

```
./scripts/pyshell dpnk --instance 0 --sys-cmd bash
```
