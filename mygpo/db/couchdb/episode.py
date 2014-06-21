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

    db_objs = Episode.objects.filter(id__in=ids)

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
