import os
import sys

import psycopg2cffi as psycopg2


if __name__ == "__main__":
    dburl = os.environ["DATABASE_URL"]
    print("Trying to connect to {}".format(dburl))
    try:
        conn = psycopg2.connect(dburl)
    except:
        print("pg connect failed, try later")
        sys.exit(-1)