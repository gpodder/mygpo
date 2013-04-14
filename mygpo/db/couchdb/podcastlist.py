from random import random

from django.core.cache import cache

from mygpo.share.models import PodcastList
from mygpo.cache import cache_result
from mygpo.db import QueryParameterMissing



# TODO: replace user_id with user
def podcastlist_for_user_slug(user_id, slug):

    if not user_id:
        raise QueryParameterMissing('user_id')

    if not slug:
        raise QueryParameterMissing('slug')

    key = 'plist-%s-%s' % (user_id, slug)

    l = cache.get(key)
    if l:
        return l

    # TODO: use user-db
    r = PodcastList.view('podcastlists/by_user_slug',
            key          = [user_id, slug],
            include_docs = True,
        )

    if r:
        l = r.one()
        cache.set(key, l, 60)
        return l

    return None



# TODO: replace user_id with user
def podcastlists_for_user(user_id):

    if not user_id:
        raise QueryParameterMissing('user_id')

    # TODO: use user-db
    r = PodcastList.view('podcastlists/by_user_slug',
            startkey = [user_id, None],
            endkey   = [user_id, {}],
            include_docs = True,
        )
    return list(r)



@cache_result(timeout=60*69)
def podcastlists_by_rating(**kwargs):
    r = PodcastList.view('podcastlists/by_rating',
            descending   = True,
            include_docs = True,
            stale        = 'update_after',
            **kwargs
        )
    return list(r)



# TODO: aggregate for all users
@cache_result(timeout=60*60)
def podcastlist_count(with_rating=True):
    view = 'podcastlists/by_rating' if with_rating else \
           'podcastlists/by_user_slug'

    return PodcastList.view(view,
            limit = 0,
            stale = 'update_after',
        ).total_rows



# TODO: aggregate for all users
def random_podcastlists(chunk_size=1):

    while True:
        rnd = random()
        res = PodcastList.view('podcastlists/random',
                startkey     = rnd,
                include_docs = True,
                limit        = chunk_size,
                stale        = 'ok',
            )

        if not res:
            break

        for r in res:
            yield r
