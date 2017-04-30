from python:3.5

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

copy requirements.freeze.txt ./
run pip install six
run pip install -r requirements.freeze.txt

copy . .

run DPNK_SECRET_KEY="fake_key" python manage.py collectstatic --noinput

EXPOSE 8000
RUN mkdir media logs
VOLUME ["logs", "media"]
ENTRYPOINT ["./docker-entrypoint.sh"]
