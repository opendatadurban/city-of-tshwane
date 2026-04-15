#! /usr/bin/env bash

# Exit in case of error
set -e

# if [ $(uname -s) = "Linux" ]; then
#     echo "Remove __pycache__ files"
#     sudo find . -type d -name __pycache__ -exec rm -r {} \+
# fi
pytest_args=$*
docker compose run --rm --build api-test $pytest_args
docker compose --profile test down --volumes


