#!/bin/sh
#
# merge-from-transifex.sh
# Fix problems with the "tx" command line client by forcing a download of
# all translations and then using the downloaded translations as a compendium
# in msgmerge to update the .po file without destroying existing content.
# ..which I think is what the "tx" client should do all along?! :/
#
# Thomas Perl <thp.io/about>; 2012-01-21
#

set -e

MERGE_DIR=../_tmp_merge_dir
MESSAGES_POT=en/LC_MESSAGES/django.po

if [ "`which tx`" = "" ]; then
    echo "The Transifex client 'tx' was not found."
    echo "If you are on Debian: apt-get install transifex-client"
    exit 1
fi

if [ "`which git`" = "" ]; then
    echo "Please install 'git'. We need it to revert changes by 'tx' ;)"
    exit 1
fi

cd `dirname $0`/../../mygpo/locale

if git status --porcelain | grep -q '^ M po'; then
    echo "Uncommitted changes in po/ - cannot continue."
    echo "Please revert or commit current changes before continuing."
    exit 1
fi

rm */LC_MESSAGES/django.po

# restore english source language
git checkout en

if [ -d "$MERGE_DIR" ]; then
    echo "The directory $MERGE_DIR still exists. Please remove it."
    exit 1
fi

# First, pull translations from Transifex, overwriting existing .po files
echo "Downloading UPDATED translations from Transifex..."
tx pull --force --all

echo "Moving files to merge directory..."
mkdir "$MERGE_DIR"

find -mindepth 1 -maxdepth 1 -not -name "en" -exec mv -v '{}' "$MERGE_DIR" \;

echo "Restoring original .po files from Git..."
git checkout .

echo "Merging translations..."

for POFILE in `find . -path ./en -prune -o -name django.po -print`; do
    echo -n "Merging $POFILE"
    msgmerge --compendium="$MERGE_DIR/$POFILE" \
             "$POFILE" "$MESSAGES_POT" --output-file="$POFILE"
done

echo "Removing merge directory..."
rm -rf "$MERGE_DIR"

echo "Running validation script to check for errors..."
sh ../../tools/i18n/validate.sh

echo "All done. Please review changes and stage them for commmit."

