#!/bin/bash -e

echo Running ruff format --check
poetry run ruff format --check apps
poetry run ruff format --check project
echo Starting tests
echo Running tests
poetry run pytest apps
#poetry run ./runtests.sh
