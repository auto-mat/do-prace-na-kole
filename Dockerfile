from auto0mat/dopracenakole-base

maintainer Automat

copy . /tmp/src
run mv /tmp/src/* .

run DPNK_SECRET_KEY="fake_key" DPNK_DEBUG_TOOLBAR=True DPNK_SILK=True poetry run python manage.py  compilemessages

run DPNK_SECRET_KEY="fake_key" DPNK_DEBUG_TOOLBAR=True DPNK_SILK=True poetry run python manage.py collectstatic --noinput

EXPOSE 8000
RUN mkdir media logs -p
VOLUME ["logs", "media"]
ENTRYPOINT ["./docker-entrypoint.sh"]
