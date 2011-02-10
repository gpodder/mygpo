#!/bin/bash

DIR=`dirname $0`
DB=`$DIR/../mygpo/print-couchdb.py`

curl -s -X GET ${DB}/_design/core/_view/podcast_by_id?limit=0
curl -s -X GET ${DB}/_design/directory/_view/toplist?limit=0
curl -s -X GET ${DB}/_design/users/_view/users_by_oldid?limit=0

