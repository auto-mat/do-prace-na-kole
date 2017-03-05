from python:3.5

maintainer Automat

run apt-get update
run apt-get install -y build-essential git
run apt-get install -y postgresql-common libpq-dev
run apt-get install -y libtiff5-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk
run apt-get install -y libxml2-dev libxslt-dev
run apt-get install -y node-less yui-compressor
run apt-get install -y libgeos-dev
run apt-get install -y gunicorn
run apt-get install -y binutils libproj-dev gdal-bin
run apt-get install -y memcached

run mkdir /home/aplikace -p
WORKDIR "/home/aplikace"

# This here for performance reasons
# if we install Django first, then we doesn't need to download it every time some dependency changes
run pip install -e git+https://github.com/PetrDlouhy/django.git@e38714cc8d5560f43cafea83cf0c9f298bee9267#egg=Django

copy requirements.freeze.txt ./
run pip install six
run pip install -r requirements.freeze.txt
copy requirements-test.txt ./
run pip install -r requirements-test.txt

copy . .

run DPNK_SECRET_KEY="fake_key" python manage.py compress
run DPNK_SECRET_KEY="fake_key" python manage.py collectstatic --noinput

EXPOSE 8000
RUN mkdir media logs
VOLUME ["logs", "media"]
ENTRYPOINT ["./docker-entrypoint.sh"]
