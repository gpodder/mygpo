#!/bin/bash
# wait-for-postgres.sh

set -e

cmd="$@"

until python contrib/psql.py; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command $cmd"
exec $cmd
