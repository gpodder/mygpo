from mygpo.directory.models import Category
from mygpo.db.couchdb import get_categories_database, get_single_result
from mygpo.cache import cache_result
from mygpo.db import QueryParameterMissing


def category_for_tag_uncached(tag):

    if not tag:
        raise QueryParameterMissing('tag')

    db = get_categories_database()
    cat = get_single_result(db, 'categories/by_tags',
            key          = tag,
            include_docs = True,
            stale        = 'update_after',
            schema       = Category
        )

    return cat


category_for_tag = cache_result(timeout=60*60)(category_for_tag_uncached)


@cache_result(timeout=60*60)
def top_categories(offset, count, with_podcasts=False):

    if offset is None:
        raise QueryParameterMissing('offset')

    if not count:
        raise QueryParameterMissing('count')

    db = get_categories_database()

    if with_podcasts:
        r = db.view('categories/by_update',
                descending   = True,
                skip         = offset,
                limit        = count,
                include_docs = True,
                stale        = 'update_after',
                schema       = Category,
            )

    else:
        r = db.view('categories/by_update',
                descending   = True,
                skip         = offset,
                limit        = count,
                stale        = 'update_after',
                wrapper      = _category_wrapper,
            )

    categories = list(r)

    for cat in categories:
        cat.set_db(db)

    return categories


def _category_wrapper(r):
    c = Category()
    c.label = r['value'][0]
    c._weight = r['value'][1]
    return c


def save_category(category):
    db = get_categories_database()
    db.save_doc(category)
