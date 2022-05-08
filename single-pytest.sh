#!/bin/bash
pytest $1 -vvv --cov-report= --cov --reuse-db --nomigrations --pdb --exitfirst
coveragepy-lcov --data_file_path .coverage --output_file_path lcov.info
sed -i 's/\/klub-v/\/home\/timothy\/pu\/auto-mat\/do-prace-na-kole/g' lcov.info
