#!/bin/bash -e

# Start Gunicorn processes
echo Starting tests
echo Installing dev dependencies
poetry install
echo Running black check
poetry run black --check --exclude migrations apps
poetry run black --check project
echo Running tests
poetry run ./runtests.sh $TEST_PARAMS
echo Generating reports
mkdir reports -p
cp htmlcov/ reports -R
cp .coverage reports/
