from collections import defaultdict
from operator import itemgetter

from mygpo.directory.models import Category
from mygpo.couch import get_main_database
from mygpo.cache import cache_result
from mygpo.db.couchdb.utils import multi_request_view
from mygpo.counter import Counter


@cache_result(timeout=60*60)
def category_for_tag(tag):
    r = Category.view('categories/by_tags',
            key          = tag,
            include_docs = True,
            stale        = 'update_after',
        )
    return r.first() if r else None


@cache_result(timeout=60*60)
def top_categories(offset, count, with_podcasts=False):
    if with_podcasts:
        r = Category.view('categories/by_update',
                descending   = True,
                skip         = offset,
                limit        = count,
                include_docs = True,
                stale        = 'update_after'
            )

    else:
        db = get_main_database()
        r = db.view('categories/by_update',
                descending   = True,
                skip         = offset,
                limit        = count,
                stale        = 'update_after',
                wrapper      = _category_wrapper,
            )

    return list(r)


def _category_wrapper(r):
    c = Category()
    c.label = r['value'][0]
    c._weight = r['value'][1]
    return c


def tags_for_podcast(podcast):
    """ all tags for the podcast, in decreasing order of importance """

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

    res = db.view('usertags/by_podcast',
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

    res = multi_request_view(db, 'usertags/podcasts',
            wrap        = False,
            reduce      = True,
            group       = True,
            group_level = 1
        )

    for r in res:
        yield r['key'][0]


@cache_result(timeout=60*60)
def toplist(res_cls, view, key, limit, **view_args):
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
