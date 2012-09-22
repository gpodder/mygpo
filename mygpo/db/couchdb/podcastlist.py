from random import random

from mygpo.share.models import PodcastList
from mygpo.cache import cache_result



def podcastlist_for_user_slug(user_id, slug):

    r = PodcastList.view('podcastlists/by_user_slug',
            key          = [user_id, slug],
            include_docs = True,
        )
    return r.first() if r else None



def podcastlists_for_user(user_id):

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



@cache_result(timeout=60*60)
def podcastlist_count(with_rating=True):
    view = 'podcastlists/by_rating' if with_rating else \
           'podcastlists/by_user_slug'

    return PodcastList.view(view,
            limit = 0,
            stale = 'update_after',
        ).total_rows



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
