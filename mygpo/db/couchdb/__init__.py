
from django.conf import settings

from couchdbkit import *


def get_main_database():
    db_url = settings.COUCHDB_DATABASES[0][1]
    return Database(db_url)


def get_database(user=None):
    return get_main_database()
