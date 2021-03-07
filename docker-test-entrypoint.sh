#!/bin/bash -e

# Start Gunicorn processes
echo Starting tests
echo Installing dev dependencies
poetry install
echo Running black check
black --check --exclude migrations apps
black --check project
echo Running tests
./runtests.sh $TEST_PARAMS
echo Generating reports
mkdir reports -p
cp htmlcov/ reports -R
cp .coverage reports/
