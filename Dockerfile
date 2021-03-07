from python:3.9-buster

maintainer Automat

run apt-get update && apt-get install -y \
   binutils \
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
   poppler-utils \
   texlive-extra-utils \
   pdftk-java \
   postgresql-common \
   postgresql-client \
   python-tk \
   tcl8.6-dev \
   tk8.6-dev \
   zlib1g-dev \
   libgettextpo-dev \
   curl

run curl -sL https://deb.nodesource.com/setup_10.x | bash -


run apt-get install -y nodejs

run mkdir /home/aplikace -p
WORKDIR "/home/aplikace"

run pip3 install poetry
run curl https://raw.githubusercontent.com/auto-mat/do-prace-na-kole/devel/poetry.lock > poetry.lock
run curl https://raw.githubusercontent.com/auto-mat/do-prace-na-kole/devel/pyproject.toml > pyproject.toml
run poetry install --no-dev
