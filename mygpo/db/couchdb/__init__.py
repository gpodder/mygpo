
from django.conf import settings

from couchdbkit import *


def get_main_database():
    db_url = settings.COUCHDB_DATABASES[0][1]
    return Database(db_url)


def get_user_database(user):
    """ returns the database in which the user's documents are stored """

    if user.db_url:
        return Database(user.db_url)

    return get_main_database()
