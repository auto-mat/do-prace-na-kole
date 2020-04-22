from auto0mat/dopracenakole-base

maintainer Automat

copy Pipfile /home/aplikace/Pipfile
copy Pipfile.lock /home/aplikace/Pipfile.lock
run pipenv install --system --ignore-pipfile --verbose --dev

copy . .

run DPNK_SECRET_KEY="fake_key" DPNK_DEBUG_TOOLBAR=True DPNK_SILK=True python manage.py collectstatic --noinput

EXPOSE 8000
RUN mkdir media logs -p
VOLUME ["logs", "media"]
ENTRYPOINT ["./docker-entrypoint.sh"]
