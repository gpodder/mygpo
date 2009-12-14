#!/usr/bin/python

import sys
import MySQLdb


try:
    mysql = MySQLdb.connect(user="mygpo_prod",passwd="",db="mygpo_prod")
    mysql_cursor = mysql.cursor() 
    
    mysql_cursor.callproc( "update_suggestion_for", (sys.argv[1]) )
    
    mysql_cursor.close() 
    mysql.close()

except MySQLdb.Error, e:
    print "MySQL Error %d:  %s" % ( e.args[0], e.args[1] )
    sys.exit(1)

except IndexError, e:
    print "Usage: python update_UserSuggestion.py [User_id]"
    sys.exit(1)
