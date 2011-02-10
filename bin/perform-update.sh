#!/bin/sh
# upgrade gpodder.net from public repository
# Stefan Kögl; 2011-02-10


BASEDIR=`dirname $0`
cd $BASEDIR/..

COUCHDB=`mygpo/print-couchdb.py`
MAINTENANCE_FILE=mygpo/MAINTENANCE_MODE


cat << EOF

   ===================================
          gpodder.net Upgrade
   ===================================

You are about to perform an upgrade of your gpodder.net installation.
Press ENTER to continue or Ctrl+C to abort...
EOF

read ME


echo -n " * Restart Webserver in Maintenace Mode... "
touch $MAINTENANCE_FILE
sudo /etc/init.d/lighttpd restart > /dev/null
echo done

echo -n "* Stashing non-committed changes... "
git stash > /dev/null
echo done

echo " * Retrieving changes from public repository... "
git pull > /dev/null
echo done

echo " * Popping stashed changes... "
git stash pop > /dev/null
echo done

echo " * Syncing Database... "
cd mygpo
./manage.py syncdb > /dev/null
cd ..
echo done

echo " * Wait for View-Updates to finish... "
bin/touch-views.sh > /dev/null
echo done


cat << EOF

Finished update procedure!

Please resolve conflicts if any
You can then start the webserver again by typing

  sudo /etc/init.d/lighttpd start

EOF
rm $MAINTENANCE_FILE

