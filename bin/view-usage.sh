#!/bin/bash
# When run on a CouchDB log file, determines the number of
# requests to individual views
# Usage: ./view-usage.sh /var/log/couchdb/couch.log

LOGFILE=$1

cat $LOGFILE | grep GET | awk '{print $13;}' | cut -f1 -d"?" | awk '{count[$1]++}END{for(j in count) print count[j],j}' | sort -n -r | head -n 10
