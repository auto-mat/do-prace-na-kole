#!/bin/bash -e

# Start Gunicorn processes
echo Starting tests
echo Running black check
poetry run black --check --exclude migrations apps
poetry run black --check project
echo Running tests
poetry run ./runtests.sh
