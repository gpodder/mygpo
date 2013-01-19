from hashlib import sha1
from datetime import datetime

from django.core.cache import cache

from mygpo.core.models import Podcast, Episode, MergedIdException
from mygpo.cache import cache_result
from mygpo.db import QueryParameterMissing
from mygpo.db.couchdb.utils import is_couchdb_id
from mygpo.db.couchdb import get_main_database
from mygpo.db.couchdb.podcast import podcast_for_url, podcast_for_slug_id


@cache_result(timeout=60*60)
def episode_by_id(episode_id, current_id=False):

    if not episode_id:
        raise QueryParameterMissing('episode_id')

    r = Episode.view('episodes/by_id',
            key          = episode_id,
            include_docs = True,
        )

    if not r:
        return None

    obj = r.one()
    if current_id and obj._id != episode_id:
        raise MergedIdException(obj, obj._id)

    return obj


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
    return list(r)


@cache_result(timeout=60*60)
def episode_for_oldid(oldid):

    if not oldid:
        raise QueryParameterMissing('oldid')

    oldid = int(oldid)
    r = Episode.view('episodes/by_oldid',
            key          = oldid,
            limit        = 1,
            include_docs = True,
        )
    return r.one() if r else None


@cache_result(timeout=60*60)
def episode_for_slug(podcast_id, episode_slug):

    if not podcast_id:
        raise QueryParameterMissing('podcast_id')

    if not episode_slug:
        raise QueryParameterMissing('episode_slug')


    r = Episode.view('episodes/by_slug',
            key          = [podcast_id, episode_slug],
            include_docs = True,
        )
    return r.first() if r else None


def episode_for_podcast_url(podcast_url, episode_url, create=False):

    if not podcast_url:
        raise QueryParameterMissing('podcast_url')

    if not episode_url:
        raise QueryParameterMissing('episode_url')


    podcast = podcast_for_url(podcast_url, create=create)

    if not podcast: # podcast does not exist and should not be created
        return None

    return episode_for_podcast_id_url(podcast.get_id(), episode_url, create)


def episode_for_podcast_id_url(podcast_id, episode_url, create=False):

    if not podcast_id:
        raise QueryParameterMissing('podcast_id')

    if not episode_url:
        raise QueryParameterMissing('episode_url')


    key = u'episode-podcastid-%s-url-%s' % (
            sha1(podcast_id.encode('utf-8')).hexdigest(),
            sha1(episode_url.encode('utf-8')).hexdigest())

    episode = cache.get(key)
    if episode:
        return episode

    r = Episode.view('episodes/by_podcast_url',
            key          = [podcast_id, episode_url],
            include_docs = True,
            reduce       = False,
        )

    if r:
        episode = r.first()
        cache.set(key, episode)
        return episode

    if create:
        episode = Episode()
        episode.podcast = podcast_id
        episode.urls = [episode_url]
        episode.save()
        cache.set(key, episode)
        return episode

    return None


@cache_result(timeout=60*60)
def episode_for_slug_id(p_slug_id, e_slug_id):
    """ Returns the Episode for Podcast Slug/Id and Episode Slug/Id """

    if not p_slug_id:
        raise QueryParameterMissing('p_slug_id')

    if not e_slug_id:
        raise QueryParameterMissing('e_slug_id')


    # The Episode-Id is unique, so take that
    if is_couchdb_id(e_slug_id):
        return episode_by_id(e_slug_id)

    # If we search using a slug, we need the Podcast's Id
    if is_couchdb_id(p_slug_id):
        p_id = p_slug_id
    else:
        podcast = podcast_for_slug_id(p_slug_id)

        if podcast is None:
            return None

        p_id = podcast.get_id()

    return episode_for_slug(p_id, e_slug_id)


@cache_result(timeout=60*60)
def episode_count():
    r = Episode.view('episodes/by_podcast',
            reduce = True,
            stale  = 'update_after',
        )
    return r.one()['value'] if r else 0


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


def episode_slugs_per_podcast(podcast_id, base_slug):

    if not podcast_id:
        raise QueryParameterMissing('podcast_id')


    res = Episode.view('episodes/by_slug',
            startkey = [podcast_id, base_slug],
            endkey   = [podcast_id, base_slug + 'ZZZZZ'],
            wrap_doc = False,
        )
    return [r['key'][1] for r in res]


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

    return list(res)


episodes_for_podcast = cache_result(timeout=60*60)(episodes_for_podcast_uncached)


@cache_result(timeout=60*60)
def episode_count_for_podcast(podcast, since=None, until={}, **kwargs):

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
            reduce       = True,
            group_level  = 1,
            **kwargs
        )

    return res.one()['value']


def favorite_episodes_for_user(user):

    if not user:
        raise QueryParameterMissing('user')

    # TODO: use user-db
    favorites = Episode.view('favorites/episodes_by_user',
            key          = user._id,
            include_docs = True,
        )
    return list(favorites)


def chapters_for_episode(episode_id):

    if not episode_id:
        raise QueryParameterMissing('episode_id')

    db = get_main_database()
    r = db.view('chapters/by_episode',
            startkey = [episode_id, None],
            endkey   = [episode_id, {}],
        )

    return map(_wrap_chapter, r)


def _wrap_chapter(res):
    from mygpo.users.models import Chapter
    user = res['key'][1]
    chapter = Chapter.wrap(res['value'])
    return (user, chapter)
