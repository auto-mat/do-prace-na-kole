from python:3.9-bullseye

maintainer Automat

RUN apt-get update && apt-get install -y \
   autossh \
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
   libev-dev \ # required for bjoern WSGI server

RUN mkdir /home/aplikace -p \
    && cd /usr/local/src/ \
    && git clone --recurse-submodules -j8 https://github.com/jonashaag/bjoern.git \
    && cd /usr/local/src/bjoern \
    && WANT_STATSD=yes WANT_STATSD_TAGS=yes make all
WORKDIR "/home/aplikace"

RUN pip3 install poetry
COPY poetry.lock .
COPY pyproject.toml .
ENV POETRY_HOME=/opt/poetry
RUN poetry install --no-dev
