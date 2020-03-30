from python:3.6

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
   python-tk \
   tcl8.6-dev \
   tk8.6-dev \
   zlib1g-dev

run mkdir /home/aplikace -p
WORKDIR "/home/aplikace"

run pip3 install pipenv
copy Pipfile /home/aplikace/Pipfile
copy Pipfile.lock /home/aplikace/Pipfile.lock
run pipenv install --system --ignore-pipfile --verbose --dev

copy . .

run DPNK_SECRET_KEY="fake_key" python manage.py collectstatic --noinput

EXPOSE 8000
RUN mkdir media logs -p
VOLUME ["logs", "media"]
ENTRYPOINT ["./docker-entrypoint.sh"]
