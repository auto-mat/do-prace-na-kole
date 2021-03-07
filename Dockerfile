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
   wget

run mkdir /home/aplikace -p
WORKDIR "/home/aplikace"

run pip3 install poetry
run wget https://raw.githubusercontent.com/auto-mat/do-prace-na-kole/devel/poetry.lock
run wget https://raw.githubusercontent.com/auto-mat/do-prace-na-kole/devel/pyproject.toml
run poetry install --no-dev
