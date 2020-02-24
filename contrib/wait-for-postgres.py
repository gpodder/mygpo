#!/usr/bin/env python
import os
import sys
import time

import psycopg2cffi as psycopg2


if __name__ == "__main__":
    dburl = os.environ["DATABASE_URL"]
    print("Trying to connect to {}".format(dburl))
    conn = None
    while not conn:
        try:
            conn = psycopg2.connect(dburl)
        except:
            print("Postgres is unavailable - sleeping")
            time.sleep(1)

    cur = conn.cursor()
    cur.execute("""SELECT EXISTS (
                  SELECT 1
                  FROM   information_schema.tables
                  WHERE  table_schema = 'public'
                  AND    table_name = 'votes_vote'
     )""")
    has_table = cur.fetchone()[0]
    cur.close()
    conn.close()

    if 'migrate' in sys.argv:
        if has_table:
            print("Database already initialized, exiting")
            sys.exit(0)
        else:
            print("Postgres is available => will initialize")
    else:
        if not has_table:
            print("ERROR: Postgres is available but not initialized.\n"
                   "Please run:\n"
                   "\tdocker-compose run web /srv/mygpo/contrib/wait-for-postgres.py python manage.py migrate\n"
                   "and restart.")
            sys.exit(-1)

    if sys.argv[1]:
        cmd = sys.argv[1:]
        print("Postgres is up - executing command {}".format(" ".join(cmd)))
        sys.stdout.flush()
        os.execvp(cmd[0], cmd)
    else:
        print("Postgres is up - no command given, exiting")