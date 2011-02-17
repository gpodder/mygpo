#!/bin/bash

COUCHDB=`mygpo/print-couchdb.py`

curl -s -H "Content-Type: application/json" -X POST $COUCHDB/_view_cleanup > /dev/null


