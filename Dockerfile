from python:3.6

maintainer Automat

run apt-get update && apt-get install -y \
   binutils \
   build-essential \
   gdal-bin \
   gettext \
   git \
   gunicorn \
   libfreetype6-dev \
   libgeos-dev \
   libjpeg-dev \
   liblcms2-dev \
   libpq-dev \
   libproj-dev \
   libtiff5-dev \
   libwebp-dev \
   libxml2-dev \
   libxslt-dev \
   memcached \
   postgresql-common \
   python-tk \
   tcl8.6-dev \
   tk8.6-dev \
   zlib1g-dev

run mkdir /home/aplikace -p
WORKDIR "/home/aplikace"

run pip3 install pipenv
copy Pipfile /home/aplikace/Pipfile
copy Pipfile.lock /home/aplikace/Pipfile.lock
run pipenv install --system --ignore-pipfile --verbose
run pip3 uninstall -y django
run pip3 install django==2.0.13 # Due to the way pipenv works it just installs packages in a more or less random order without actually garanteeing version constraints in the Pipfile are fulfilled in case those packages are installed as dependencies of other packages. If we really want to have a specific django version we have to install it manually.

copy . .

run DPNK_SECRET_KEY="fake_key" python manage.py collectstatic --noinput

EXPOSE 8000
RUN mkdir media logs
VOLUME ["logs", "media"]
ENTRYPOINT ["./docker-entrypoint.sh"]
