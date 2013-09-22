from collections import defaultdict, Counter
from operator import itemgetter

from mygpo.directory.models import Category
from mygpo.db.couchdb import get_main_database, get_categories_database, \
    get_userdata_database
from mygpo.cache import cache_result
from mygpo.db.couchdb.utils import multi_request_view
from mygpo.db import QueryParameterMissing


@cache_result(timeout=60*60)
def category_for_tag(tag):

    if not tag:
        raise QueryParameterMissing('tag')

    db = get_categories_database()
    r = db.view('categories/by_tags',
            key          = tag,
            include_docs = True,
            stale        = 'update_after',
            schema       = Category
        )

    if r:
        cat = r.first()
        cat.set_db(db)
        return cat

    else:
        return None


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


def tags_for_podcast(podcast):
    """ all tags for the podcast, in decreasing order of importance """

    if not podcast:
        raise QueryParameterMissing('podcast')


    db = get_main_database()
    res = db.view('tags/by_podcast',
            startkey    = [podcast.get_id(), None],
            endkey      = [podcast.get_id(), {}],
            reduce      = True,
            group       = True,
            group_level = 2,
            stale       = 'update_after',
        )

    tags = Counter(dict((x['key'][1], x['value']) for x in res))

    udb = get_userdata_database()
    res = udb.view('usertags/by_podcast',
            startkey    = [podcast.get_id(), None],
            endkey      = [podcast.get_id(), {}],
            reduce      = True,
            group       = True,
            group_level = 2,
        )

    tags.update(Counter(dict( (x['key'][1], x['value']) for x in res)))

    get_tag = itemgetter(0)
    return map(get_tag, tags.most_common())


def tags_for_user(user, podcast_id=None):
    """ mapping of all podcasts tagged by the user with a list of tags """

    if not user:
        raise QueryParameterMissing('user')


    db = get_main_database()
    res = db.view('tags/by_user',
            startkey = [user._id, podcast_id],
            endkey   = [user._id, podcast_id or {}]
        )

    tags = defaultdict(list)
    for r in res:
        tags[r['key'][1]].append(r['value'])
    return tags


def all_tags():
    """ Returns all tags

    Some tags might be returned twice """
    db = get_main_database()
    res = multi_request_view(db, 'podcasts/by_tag',
            wrap        = False,
            reduce      = True,
            group       = True,
            group_level = 1
        )

    for r in res:
        yield r['key'][0]

    udb = get_userdata_database()
    res = multi_request_view(udb, 'usertags/podcasts',
            wrap        = False,
            reduce      = True,
            group       = True,
            group_level = 1
        )

    for r in res:
        yield r['key'][0]


@cache_result(timeout=60*60)
def toplist(res_cls, view, key, limit, **view_args):

    if not limit:
        raise QueryParameterMissing('limit')


    r = res_cls.view(view,
            startkey     = key + [{}],
            endkey       = key + [None],
            include_docs = True,
            descending   = True,
            limit        = limit,
            stale        = 'update_after',
            **view_args
        )
    return list(r)
