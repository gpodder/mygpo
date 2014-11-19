#!/bin/bash
# Docker doesn't have a great way to set environment variables at startup.
# This scripts will set up some defaults.

# if a DATABSE_URL is provided from outside, use it
if [[ -z "$DATABASE_URL" ]]; then
    # otherwise construct one using a linked "db" container
    export DATABASE_URL="postgres://mygpo:mygpo@${DB_PORT_5432_TCP_ADDR}:5432/mygpo"
fi

# if not SECRET_KEY is provided from outside, create a random one
if [[ -z "$SECRET_KEY" ]]; then
    export SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
fi

# Execute the commands passed to this script
exec "$@"
