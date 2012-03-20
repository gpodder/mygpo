from operator import itemgetter

from couchdbkit import *


def __default_reload(db, obj):
    _id = getattr(obj, '_id', obj.get('_id', None))

    if isinstance(obj, Document):
        return obj.__class__.get(_id)
    else:
        return db[_id]


__get_obj = itemgetter(0)

def bulk_save_retry(db, obj_funs, reload_f=__default_reload):
    """ Saves multiple documents and retries failed ones

    Objects to be saved are passed as (obj, mod_f), where obj is the CouchDB
    and mod_f is the modification function that should be applied to it.

    If saving a document fails, it is again fetched from the database, the
    modification function is applied again and saving is retried. """

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
                if res.get('error', False):

                    # reload conflicted object
                    obj = reload_f(db, obj)
                    new_obj_funs.append( (obj, f) )

            obj_funs = new_obj_funs
