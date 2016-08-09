#!/bin/bash

# if not SECRET_KEY is provided from outside, create a random one
if [[ -z "$SECRET_KEY" ]]; then
    export SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
fi

# Execute the commands passed to this script
exec "$@"
