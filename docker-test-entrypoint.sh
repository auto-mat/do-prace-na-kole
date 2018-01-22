#!/bin/bash -e

# Start Gunicorn processes
echo Starting tests
pip install -r requirements-test.txt
flake8
./runtests.sh $TEST_PARAMS
mkdir reports -p
pip freeze > reports/requirements.freeze.txt
cp htmlcov/ reports -R
cp .coverage reports/
