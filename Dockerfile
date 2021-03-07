from auto0mat/dopracenakole-base

maintainer Automat

copy poetry.lock /home/aplikace/poetry.lock
copy pyproject.toml /home/aplikace/pyproject.toml
env POETRY_HOME=/opt/poetry
run poetry install --no-dev

copy . .

run DPNK_SECRET_KEY="fake_key" DPNK_DEBUG_TOOLBAR=True DPNK_SILK=True poetry run python manage.py collectstatic --noinput

EXPOSE 8000
RUN mkdir media logs -p
VOLUME ["logs", "media"]
ENTRYPOINT ["./docker-entrypoint.sh"]
