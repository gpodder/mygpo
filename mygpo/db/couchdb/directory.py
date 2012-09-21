from mygpo.directory.models import Category
from mygpo.couch import get_main_database
from mygpo.cache import cache_result


@cache_result(timeout=60*60)
def category_for_tag(tag):
    r = Category.view('categories/by_tags',
            key          = tag,
            include_docs = True,
            stale        = 'update_after',
        )
    return r.first() if r else None


@cache_result(timeout=60*60)
def top_categories(count, wrap=True):
    if wrap:
        src = Category
    else:
        src = get_main_database()

    r = src.view('categories/by_weight',
            descending   = True,
            limit        = count,
            include_docs = True,
            stale        = 'update_after',
        )
    return list(r)



def tags_for_podcast(podcast):
    """ all tags for the podcast, in decreasing order of importance """

    res = Podcast.view('tags/by_podcast',
            startkey    = [podcast.get_id(), None],
            endkey      = [podcast.get_id(), {}],
            reduce      = True,
            group       = True,
            group_level = 2,
            stale       = 'update_after',
        )

    tags = Counter(dict((x['key'][1], x['value']) for x in res))

    res = Podcast.view('usertags/by_podcast',
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

    res = Podcast.view('tags/by_user',
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
    res = multi_request_view(Podcast, 'podcasts/by_tag',
            wrap        = False,
            reduce      = True,
            group       = True,
            group_level = 1
        )

    for r in res:
        yield r['key'][0]

    res = multi_request_view(Podcast, 'usertags/podcasts',
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
