from mygpo.db.couchdb import get_main_database
from mygpo.db import QueryParameterMissing, get_single_result
from mygpo.db.couchdb.utils import multi_request_view


def missing_slug_count(doc_type, start, end):

    if not doc_type:
        raise QueryParameterMissing('doc_type')

    if not start:
        raise QueryParameterMissing('start')

    if not end:
        raise QueryParameterMissing('end')


    db = get_main_database()
    res = get_single_result(db, 'slugs/missing',
            startkey     = [doc_type] + end,
            endkey       = [doc_type] + start,
            descending   = True,
            reduce       = True,
            group        = True,
            group_level  = 1,
        )
    return res['value'] if res else 0


def missing_slugs(doc_type, start, end, wrapper, **kwargs):

    if not doc_type:
        raise QueryParameterMissing('doc_type')

    if not start:
        raise QueryParameterMissing('start')

    if not end:
        raise QueryParameterMissing('end')


    db = get_main_database()
    return multi_request_view(db, 'slugs/missing',
            startkey     = [doc_type] + end,
            endkey       = [doc_type] + start,
            descending   = True,
            include_docs = True,
            reduce       = False,
            wrapper      = wrapper,
            auto_advance = False,
            **kwargs
        )
