#!/bin/bash -e

# Start Gunicorn processes
echo Starting tests
pipenv install --dev --system
flake8
./runtests.sh $TEST_PARAMS
mkdir reports -p
cp htmlcov/ reports -R
cp .coverage reports/
