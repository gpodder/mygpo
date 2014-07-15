from random import random

from django.core.cache import cache

from mygpo.podcasts.models import Podcast
from mygpo.utils import get_timestamp
from mygpo.share.models import PodcastList
from mygpo.cache import cache_result
from mygpo.decorators import repeat_on_conflict
from mygpo.db import QueryParameterMissing
from mygpo.db.couchdb import get_podcastlists_database, get_single_result


def podcastlist_for_user_slug(user_id, slug):

    if not user_id:
        raise QueryParameterMissing('user_id')

    if not slug:
        raise QueryParameterMissing('slug')

    pdb = get_podcastlists_database()
    l = get_single_result(pdb, 'podcastlists/by_user_slug',
            key          = [user_id, slug],
            include_docs = True,
            schema       = PodcastList,
        )

    return l



def podcastlists_for_user(user_id):

    if not user_id:
        raise QueryParameterMissing('user_id')

    pdb = get_podcastlists_database()
    r = pdb.view('podcastlists/by_user_slug',
            startkey = [user_id, None],
            endkey   = [user_id, {}],
            include_docs = True,
            schema   = PodcastList,
        )
    return list(r)



@cache_result(timeout=60*69)
def podcastlists_by_rating(**kwargs):
    pdb = get_podcastlists_database()
    r = pdb.view('podcastlists/by_rating',
            descending   = True,
            include_docs = True,
            stale        = 'update_after',
            schema       = PodcastList,
            **kwargs
        )
    return list(r)



@cache_result(timeout=60*60)
def podcastlist_count(with_rating=True):
    view = 'podcastlists/by_rating' if with_rating else \
           'podcastlists/by_user_slug'

    pdb = get_podcastlists_database()
    return pdb.view(view,
            limit = 0,
            stale = 'update_after',
        ).total_rows



def random_podcastlists(chunk_size=1):

    pdb = get_podcastlists_database()
    while True:
        rnd = random()
        res = pdb.view('podcastlists/random',
                startkey     = rnd,
                include_docs = True,
                limit        = chunk_size,
                stale        = 'ok',
                schema       = PodcastList,
            )

        if not res:
            break

        for r in res:
            yield r


@repeat_on_conflict(['plist'])
def add_podcast_to_podcastlist(plist, podcast_id):
    pdb = get_podcastlists_database()
    plist.podcasts.append(podcast_id)
    pdb.save_doc(plist)


@repeat_on_conflict(['plist'])
def remove_podcast_from_podcastlist(plist, podcast_id):

    pdb = get_podcastlists_database()

    if podcast_id in plist.podcasts:
        plist.podcasts.remove(podcast_id)

    if not podcast_id in plist.podcasts:
        # the podcast might be there with another id
        podcast = Podcast.objects.get(id=podcast_id)
        podcast_id = podcast.get_id()
        if podcast_id in plist.podcasts:
            plist.podcasts.remove(podcast_id)

    pdb.save_doc(plist)


@repeat_on_conflict(['plist'])
def delete_podcastlist(plist):
    pdb = get_podcastlists_database()
    pdb.delete_doc(plist)


def create_podcast_list(title, slug, user_id, created):
    pdb = get_podcastlists_database()
    plist = PodcastList()
    plist.created_timestamp = get_timestamp(created)
    plist.title = title
    plist.slug = slug
    plist.user = user_id
    pdb.save_doc(plist)
