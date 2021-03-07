#!/bin/bash -e

# Start Gunicorn processes
echo Starting tests
poetry install --dev --system
black --check --exclude migrations apps
black --check project
flake8
./runtests.sh $TEST_PARAMS
mkdir reports -p
cp htmlcov/ reports -R
cp .coverage reports/
