#!/bin/bash -e

# Start Gunicorn processes
echo Starting tests
pip install -r requirements-test.freeze.txt
flake8
pip install "$DJANGO_VERSION"
./runtests.sh $TEST_PARAMS
mkdir reports -p
pip freeze > reports/requirements.freeze.txt
cp htmlcov/ reports -R
cp .coverage reports/
