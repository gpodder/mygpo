
# Fix a bug where older versions of mygpo allowed users to set the
# UID to the same value for different devices. This is not allowed
# anymore by update-12.sql from January 2010, but it is needed for
# migrating the existing user database. -- Thomas Perl, 2010-01-19

import MySQLdb
import sys

if len(sys.argv) != 3:
    print >>sys.stderr, """
    Usage: %s [username] [database]
    """ % (sys.argv[0],)
    sys.exit(1)

username, database = sys.argv[-2:]
connection = MySQLdb.connect(user=username, db=database)

cur = connection.cursor()
cur.execute('select uid, user_id, count(*) from device'
          +' group by uid, user_id having count(*) > 1')
todo = list(cur.fetchall())
cur.close()

cur = connection.cursor()
for uid, user_id, count in todo:
    counter = 1
    cur.execute('select id from device where uid=%s and user_id=%s',
            (uid, user_id))
    for row in list(cur.fetchall()):
        id = row[0]
        if counter > 1:
            new_uid = '%s%d' % (uid, counter)
            print 'updating uid of %s to %s' % (id, new_uid)
            cur.execute('update device set uid=%s where id=%s',
                    (new_uid, id))
        counter += 1
cur.close()

connection.close()

