#!/bin/bash

DIR=`dirname $0`
DB=`$DIR/../mygpo/print-couchdb.py`

echo -n "Touching View core ...                 "
curl -s -X GET ${DB}/_design/core/_view/podcasts_by_id?limit=0 > /dev/null
echo done

echo -n "Touching View directory ...            "
curl -s -X GET ${DB}/_design/directory/_view/toplist?limit=0 > /dev/null
echo done

echo -n "Touching View users ...                "
curl -s -X GET ${DB}/_design/users/_view/users_by_oldid?limit=0 > /dev/null
echo done

echo -n "Touching View django_couchdb_utils ... "
curl -s -X GET ${DB}/_design/django_couchdb_utils/_view/emails?limit=0 > /dev/null
echo done
