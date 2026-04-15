#!/usr/bin/env bash
#TODO fix this script
NOTES=$1
cd ..
REVISION_FILE=$(docker compose exec api alembic revision --autogenerate -m $NOTES 2>&1 | grep "Generating" | awk -F'Generating ' '{print $2}' | sed 's/\.py.*/.py/')
docker compose cp api:$REVISION_FILE ./src/app/alembic/versions/
