from operator import itemgetter
from collections import namedtuple

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


class BulkException(Exception):

    def __init__(self, errors):
        self.errors = errors


BulkError = namedtuple('BulkError', 'doc error reason')


def __default_reload(db, obj):
    _id = obj._id

    if isinstance(obj, Document):
        return obj.__class__.get(_id)
    else:
        return db[_id]


__get_obj = itemgetter(0)

def bulk_save_retry(obj_funs, db=None, reload_f=__default_reload):
    """ Saves multiple documents and retries failed ones

    Objects to be saved are passed as (obj, mod_f), where obj is the CouchDB
    and mod_f is the modification function that should be applied to it.

    If saving a document fails, it is again fetched from the database, the
    modification function is applied again and saving is retried. """

    db = db or get_main_database()
    errors = []

    while True:

        # apply modification function (and keep funs)
        obj_funs = [(f(o), f) for (o, f) in obj_funs]

        # filter those with obj None
        obj_funs = filter(lambda of: __get_obj(of) is not None, obj_funs)

        # extract objects
        objs = map(__get_obj, obj_funs)

        if not objs:
            return

        try:
            db.save_docs(objs)
            return

        except BulkSaveError as ex:

            new_obj_funs = []
            for res, (obj, f) in zip(ex.results, obj_funs):
                if res.get('error', False) == 'conflict':

                    # reload conflicted object
                    obj = reload_f(db, obj)
                    new_obj_funs.append( (obj, f) )

                elif res.get('error', False):
                    # don't retry other errors
                    err = BulkError(obj, res['error'], res.get('reason', None))
                    errors.append(err)

            obj_funs = new_obj_funs

    if errors:
        raise BulkException(errors)
