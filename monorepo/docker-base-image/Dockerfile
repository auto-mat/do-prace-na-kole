from python:3.9-bullseye

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
   postgresql-common \
   postgresql-client \
   tcl8.6-dev \
   zlib1g-dev \
   libgettextpo-dev \
   curl \
   pdftk-java \
   postgis \
   fuse3 \
   s3fs \
   npm

run mkdir /home/aplikace -p \
    && npm install -g bower
WORKDIR "/home/aplikace"

run pip3 install poetry
copy poetry.lock .
copy pyproject.toml .
env POETRY_HOME=/opt/poetry
run poetry install --no-dev
