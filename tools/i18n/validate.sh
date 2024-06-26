#!/bin/sh

set -e

for translation in `dirname $0`/../../mygpo/locale/*/LC_MESSAGES/django.po; do
    echo "Checking: $translation"
    msgfmt --check "$translation"
done

