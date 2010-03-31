#!/bin/sh
# my.gpodder.org initial database setup
# Thomas Perl; 2010-03-31

USER=mygpo
DB=mygpo

LOGFILE=install.log
SQL_SCRIPTS="create-db.sql update-*.sql sanitizing-rules.sql"

MYSQL="mysql -u $USER $DB -vv"

cat <<EOF

   ===================================
   my.gpodder.org Initial Installation
   ===================================

  THIS SCRIPT IS INTENDED FOR INITIAL INSTALLATION ONLY.
  DO NOT USE THIS SCRIPT IF YOU ARE UPGRADING YOUR DB!!!

Press ENTER to continue or Ctrl+C to abort...
EOF

read ME

(for file in $SQL_SCRIPTS; do
    $MYSQL < $file || exit 1
done) 2>&1 | tee $LOGFILE

cat <<EOF

  If you can read this, there is a high probability that
  everything went okay. Please check the screen output
  for details. In case of problems, the output has been
  written to a file that you can use for bug reporting:

        $LOGFILE

EOF

