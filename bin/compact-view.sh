#!/bin/bash

VIEW=$1
COUCHDB=`mygpo/print-couchdb.py`

curl -s -H "Content-Type: application/json" -X POST $COUCHDB/_compact/$VIEW


