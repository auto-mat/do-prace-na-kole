from auto0mat/dopracenakole-base

maintainer Automat

COPY . /tmp/src
RUN mv /tmp/src/* . \
    && DPNK_SECRET_KEY="fake_key" DPNK_DEBUG_TOOLBAR=True DPNK_SILK=True poetry run python manage.py compilemessages \
    && DPNK_SECRET_KEY="fake_key" DPNK_DEBUG_TOOLBAR=True DPNK_SILK=True poetry run python manage.py collectstatic --noinput
    && mkdir media logs -p
    && chmod +x wsgi.py
EXPOSE 8000
ENTRYPOINT ["./docker-entrypoint.sh"]
