from hashlib import sha1
from datetime import datetime
from collections import Counter

from django.core.cache import cache

from mygpo.podcasts.models import Podcast
from mygpo.core.models import Episode, MergedIdException
from mygpo.core.signals import incomplete_obj
from mygpo.cache import cache_result
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import get_timestamp
from mygpo.db import QueryParameterMissing
from mygpo.db.couchdb import get_main_database, get_single_result

import logging
logger = logging.getLogger(__name__)


@cache_result(timeout=60*60)
def episode_by_id(episode_id, current_id=False):

    if not episode_id:
        raise QueryParameterMissing('episode_id')

    db = get_main_database()

    episode = get_single_result(db, 'episodes/by_id',
            key          = episode_id,
            include_docs = True,
            schema       = Episode,
        )

    if not episode:
        return None

    if current_id and episode._id != episode_id:
        raise MergedIdException(episode, episode._id)

    if episode.needs_update:
        incomplete_obj.send_robust(sender=episode)

    return episode


@cache_result(timeout=60*60)
def episodes_by_id(episode_ids):

    if episode_ids is None:
        raise QueryParameterMissing('episode_ids')

    if not episode_ids:
        return []

    r = Episode.view('episodes/by_id',
            include_docs = True,
            keys         = episode_ids,
        )

    episodes = list(r)

    for episode in episodes:
        if episode.needs_update:
            incomplete_obj.send_robust(sender=episode)

    return episodes


def episode_for_podcast_url(podcast_url, episode_url, create=False):

    if not podcast_url:
        raise QueryParameterMissing('podcast_url')

    if not episode_url:
        raise QueryParameterMissing('episode_url')


    if create:
        podcast = Podcast.objects.get_or_create_for_url(podcast_url)

    else:
        try:
            podcast = Podcast.objects.get(urls__url=podcast_url)
        except Podcast.DoesNotExist:
            # podcast does not exist and should not be created
            return None

    return episode_for_podcast_id_url(podcast.id, episode_url, create)


def episodes_to_dict(ids, use_cache=False):

    if ids is None:
        raise QueryParameterMissing('ids')

    if not ids:
        return {}


    ids = list(set(ids))
    objs = dict()

    cache_objs = []
    if use_cache:
        res = cache.get_many(ids)
        cache_objs.extend(res.values())
        ids = [x for x in ids if x not in res.keys()]

    db_objs = list(episodes_by_id(ids))

    for obj in (cache_objs + db_objs):

        # get_multi returns dict {'key': _id, 'error': 'not found'}
        # for non-existing objects
        if isinstance(obj, dict) and 'error' in obj:
            _id = obj['key']
            objs[_id] = None
            continue

        for i in obj.get_ids():
            objs[i] = obj

    if use_cache:
        cache.set_many(dict( (obj._id, obj) for obj in db_objs))

    return objs


def episodes_for_podcast_uncached(podcast, since=None, until={}, **kwargs):

    if not podcast:
        raise QueryParameterMissing('podcast')


    if kwargs.get('descending', False):
        since, until = until, since

    if isinstance(since, datetime):
        since = since.isoformat()

    if isinstance(until, datetime):
        until = until.isoformat()

    res = Episode.view('episodes/by_podcast',
            startkey     = [podcast.get_id(), since],
            endkey       = [podcast.get_id(), until],
            include_docs = True,
            reduce       = False,
            **kwargs
        )

    episodes = list(res)

    for episode in episodes:
        if episode.needs_update:
            incomplete_obj.send_robust(sender=episode)

    return episodes


episodes_for_podcast = cache_result(timeout=60*60)(episodes_for_podcast_uncached)


def favorite_episodes_for_user(user):
    episode_ids = list(favorite_episode_ids_for_user(user))
    return episodes_by_id(episode_ids)


def filetype_stats():
    """ Returns a filetype counter over all episodes """

    db = get_main_database()
    r = db.view('episode_stats/filetypes',
        stale       = 'update_after',
        reduce      = True,
        group_level = 1,
    )

    return Counter({x['key']: x['value'] for x in r})


@repeat_on_conflict(['episode'])
def set_episode_slug(episode, slug):
    """ sets slug as new main slug of the episode, moves other to merged """
    episode.set_slug(slug)
    episode.save()


@repeat_on_conflict(['episode'])
def remove_episode_slug(episode, slug):
    """ removes slug from main and merged slugs """
    episode.remove_slug(slug)
    episode.save()


@repeat_on_conflict(['episode'])
def set_episode_listeners(episode, listeners):

    if episode.listeners == listeners:
        return False

    episode.listeners = listeners

    db = get_main_database()
    db.save_doc(episode)
    return True
