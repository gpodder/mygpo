from hashlib import sha1
from datetime import datetime
from dateutil import parser

from django.core.cache import cache

from mygpo.podcasts.models import Podcast, Episode
from mygpo.users.models import EpisodeUserState
from mygpo.db import QueryParameterMissing
from mygpo.db.couchdb import get_main_database, get_userdata_database, \
     get_single_result
from mygpo.cache import cache_result
from mygpo.decorators import repeat_on_conflict



def episode_state_for_user_episode(user, episode):

    if not user:
        raise QueryParameterMissing('user')

    if not episode:
        raise QueryParameterMissing('episode')

    if hasattr(episode, '_id'):
        episode_id = episode._id
    else:
        episode_id = episode.get_id()
    key = 'episode-state-userid-%s-episodeid-%s' % (sha1(user._id).hexdigest(),
            sha1(episode_id).hexdigest())

#   Disabled as cache invalidation does not work properly
#   state = cache.get(key)
#   if state:
#       return state

    udb = get_userdata_database()
    state = get_single_result(udb, 'episode_states/by_user_episode',
            key          = [user._id, episode_id],
            include_docs = True,
            limit        = 1,
            schema       = EpisodeUserState,
        )

    if state:
        cache.set(key, state)
        return state

    else:
        if isinstance(episode.podcast, unicode):
            podcast = Podcast.objects.get_by_any_id(episode.podcast)
        else:
            podcast = episode.podcast

        state = EpisodeUserState()
        state.episode = episode_id
        state.podcast = podcast.get_id()
        state.user = user._id
        state.ref_url = episode.url
        state.podcast_ref_url = podcast.url
        # don't cache here, because the state is saved by the calling function

        return state



def all_episode_states(episode):

    if not episode:
        raise QueryParameterMissing('episode')

    if isinstance(episode.podcast, unicode):
        podcast_id = episode.podcast
    else:
        podcast_id = episode.podcast.get_id()

    if hasattr(episode, '_id'):
        episode_id = episode._id
    else:
        episode_id = episode.get_id()

    udb = get_userdata_database()
    r = udb.view('episode_states/by_podcast_episode',
            startkey     = [podcast_id, episode_id, None],
            endkey       = [podcast_id, episode_id, {}],
            include_docs = True,
            schema       = EpisodeUserState,
        )

    states = list(r)

    for state in states:
        state.set_db(udb)

    return states



def all_podcast_episode_states(podcast):

    if not podcast:
        raise QueryParameterMissing('podcast')

    udb = get_userdata_database()
    r = udb.view('episode_states/by_podcast_episode',
            startkey     = [podcast.get_id(), None, None],
            endkey       = [podcast.get_id(), {},   {}],
            include_docs = True,
            schema       = EpisodeUserState,
        )

    states = list(r)

    for state in states:
        state.set_db(udb)

    return states



@cache_result(timeout=60*60)
def podcast_listener_count(episode):
    """ returns the number of users that have listened to this podcast """

    if not episode:
        raise QueryParameterMissing('episode')

    udb = get_userdata_database()
    r = get_single_result(udb, 'listeners/by_podcast',
            startkey    = [episode.get_id(), None],
            endkey      = [episode.get_id(), {}],
            group       = True,
            group_level = 1,
            reduce      = True,
            stale       = 'update_after',
        )
    return r['value'] if r else 0


@cache_result(timeout=60*60)
def podcast_listener_count_timespan(podcast, start=None, end={}):
    """ returns (date, listener-count) tuples for all days w/ listeners """

    if not podcast:
        raise QueryParameterMissing('podcast')

    if isinstance(start, datetime):
        start = start.isoformat()

    if isinstance(end, datetime):
        end = end.isoformat()

    udb = get_userdata_database()
    r = udb.view('listeners/by_podcast',
            startkey    = [podcast.get_id(), start],
            endkey      = [podcast.get_id(), end],
            group       = True,
            group_level = 2,
            reduce      = True,
            stale       = 'update_after',
        )

    return map(_wrap_listener_count, r)


@cache_result(timeout=60*60)
def episode_listener_counts(episode):
    """ (Episode-Id, listener-count) tuples for episodes w/ listeners """

    if not episode:
        raise QueryParameterMissing('episode')

    udb = get_userdata_database()
    r = udb.view('listeners/by_podcast_episode',
            startkey    = [episode.get_id(), None, None],
            endkey      = [episode.get_id(), {},   {}],
            group       = True,
            group_level = 2,
            reduce      = True,
            stale       = 'update_after',
        )

    return map(_wrap_listeners, r)



def get_podcasts_episode_states(podcast, user_id):
    """ Returns the latest episode actions for the podcast's episodes """

    if not podcast:
        raise QueryParameterMissing('podcast')

    if not user_id:
        raise QueryParameterMissing('user_id')

    udb = get_userdata_database()
    res = udb.view('episode_states/by_user_podcast',
            startkey = [user_id, podcast.get_id(), None],
            endkey   = [user_id, podcast.get_id(), {}],
        )

    return map(lambda r: r['value'], res)



@cache_result(timeout=60*60)
def episode_listener_count(episode, start=None, end={}):
    """ returns the number of users that have listened to this episode """

    if not episode:
        raise QueryParameterMissing('episode')

    udb = get_userdata_database()
    r = get_single_result(udb, 'listeners/by_episode',
            startkey    = [episode.id, start],
            endkey      = [episode.id, end],
            group       = True,
            group_level = 2,
            reduce      = True,
            stale       = 'update_after',
        )
    return r['value'] if r else 0



@cache_result(timeout=60*60)
def episode_listener_count_timespan(episode, start=None, end={}):
    """ returns (date, listener-count) tuples for all days w/ listeners """

    if not episode:
        raise QueryParameterMissing('episode')


    if isinstance(start, datetime):
        start = start.isoformat()

    if isinstance(end, datetime):
        end = end.isoformat()

    udb = get_userdata_database()
    r = udb.view('listeners/by_episode',
            startkey    = [episode._id, start],
            endkey      = [episode._id, end],
            group       = True,
            group_level = 3,
            reduce      = True,
            stale       = 'update_after',
        )

    return map(_wrap_listener_count, r)



def episode_state_for_ref_urls(user, podcast_url, episode_url):

    if not user:
        raise QueryParameterMissing('user')

    if not podcast_url:
        raise QueryParameterMissing('podcast_url')

    if not episode_url:
        raise QueryParameterMissing('episode_url')


    cache_key = 'episode-state-%s-%s-%s' % (user._id,
            sha1(podcast_url).hexdigest(),
            sha1(episode_url).hexdigest())

    state = cache.get(cache_key)
    if state:
        return state

    udb = get_userdata_database()
    state = get_single_result(udb, 'episode_states/by_ref_urls',
            key   = [user._id, podcast_url, episode_url],
            limit = 1,
            include_docs=True,
            schema      = EpisodeUserState,
        )

    if state:
        state.ref_url = episode_url
        state.podcast_ref_url = podcast_url
        cache.set(cache_key, state, 60*60)
        return state

    else:
        podcast = Podcast.objects.get_or_create_for_url(podcast_url)
        episode = Episode.objects.get_or_create_for_url(podcast, episode_url)
        return episode_state_for_user_episode(user, episode)



def get_episode_actions(user_id, since=None, until={}, podcast_id=None,
           device_id=None, limit=1000):
    """ Returns Episode Actions for the given criteria

    There is an upper limit on how many actions will be returned; until is the
    timestamp of the last episode action.
    """

    if not user_id:
        raise QueryParameterMissing('user_id')

    if since >= until:
        return [], until

    if not podcast_id and not device_id:
        view = 'episode_actions/by_user'
        startkey = [user_id, since]
        endkey   = [user_id, until]

    elif podcast_id and not device_id:
        view = 'episode_actions/by_podcast'
        startkey = [user_id, podcast_id, since]
        endkey   = [user_id, podcast_id, until]

    elif device_id and not podcast_id:
        view = 'episode_actions/by_device'
        startkey = [user_id, device_id, since]
        endkey   = [user_id, device_id, until]

    else:
        view = 'episode_actions/by_podcast_device'
        startkey = [user_id, podcast_id, device_id, since]
        endkey   = [user_id, podcast_id, device_id, until]

    udb = get_userdata_database()
    res = udb.view(view,
            startkey = startkey,
            endkey   = endkey,
            limit    = limit,
        )

    results = list(res)
    actions = map(lambda r: r['value'], results)
    if actions:
        # the upload_timestamp is always the last part of the key
        until = results[-1]['key'][-1]

    return actions, until



@cache_result(timeout=60*60)
def episode_states_count():
    udb = get_userdata_database()
    r = udb.view('episode_states/by_user_episode',
            limit = 0,
            stale = 'update_after',
        )
    return r.total_rows


def get_nth_episode_state(n):
    udb = get_userdata_database()
    state = get_single_result(udb, 'episode_states/by_user_episode',
            skip         = n,
            include_docs = True,
            limit        = 1,
            schema       = EpisodeUserState,
        )

    return state


def get_duplicate_episode_states(user, episode):

    if not user:
        raise QueryParameterMissing('user')

    if not episode:
        raise QueryParameterMissing('episode')

    udb = get_userdata_database()
    r = udb.view('episode_states/by_user_episode',
            key          = [user, episode],
            include_docs = True,
            schema       = EpisodeUserState,
        )

    states = list(r)

    for state in states:
        state.set_db(udb)

    return states


def _wrap_listener_count(res):
    date = parser.parse(res['key'][1]).date()
    listeners = res['value']
    return (date, listeners)


def _wrap_listeners(res):
    episode   = res['key'][1]
    listeners = res['value']
    return (episode, listeners)


@cache_result(timeout=60*60)
def get_heatmap(podcast_id, episode_id, user_id):
    udb = get_userdata_database()

    group_level = len(filter(None, [podcast_id, episode_id, user_id]))

    r = udb.view('heatmap/by_episode',
            startkey    = [podcast_id, episode_id,       user_id],
            endkey      = [podcast_id, episode_id or {}, user_id or {}],
            reduce      = True,
            group       = True,
            group_level = group_level,
            stale       = 'update_after',
        )

    if not r:
        return [], []

    else:
        res = r.first()['value']
        return res['heatmap'], res['borders']


@repeat_on_conflict(['state'])
def add_episode_actions(state, actions):
    udb = get_userdata_database()
    state.add_actions(actions)
    udb.save_doc(state)


@repeat_on_conflict(['state'])
def update_episode_state_object(state, podcast_id, episode_id=None):
    state.podcast = podcast_id

    if episode_id is not None:
        state.episode = episode_id

    udb = get_userdata_database()
    udb.save_doc(state)


@repeat_on_conflict(['state'])
def merge_episode_states(state, state2):
    state.add_actions(state2.actions)

    # overwrite settings in state2 with state's settings
    settings = state2.settings
    settings.update(state.settings)
    state.settings = settings

    merged_ids = set(state.merged_ids + [state2._id] + state2.merged_ids)
    state.merged_ids = filter(None, merged_ids)

    state.chapters = list(set(state.chapters + state2.chapters))

    udb = get_userdata_database()
    udb.save_doc(state)


@repeat_on_conflict(['state'])
def delete_episode_state(state):
    udb = get_userdata_database()
    udb.delete_doc(state)


@repeat_on_conflict(['episode_state'])
def update_episode_chapters(episode_state, add=[], rem=[]):
    """ Updates the Chapter list

     * add contains the chapters to be added

     * rem contains tuples of (start, end) times. Chapters that match
       both endpoints will be removed
    """

    for chapter in add:
        episode_state.chapters = episode_state.chapters + [chapter]

    for start, end in rem:
        keep = lambda c: c.start != start or c.end != end
        episode_state.chapters = filter(keep, episode_state.chapters)

    episode_state.save()


def favorite_episode_ids_for_user(user):

    if not user:
        raise QueryParameterMissing('user')

    udb = get_userdata_database()
    favorites = udb.view('favorites/episodes_by_user',
            key = user._id,
        )

    return set(x['value']['_id'] for x in favorites)


def chapters_for_episode(episode_id):

    if not episode_id:
        raise QueryParameterMissing('episode_id')

    udb = get_userdata_database()
    r = udb.view('chapters/by_episode',
            startkey = [episode_id, None],
            endkey   = [episode_id, {}],
        )

    return map(_wrap_chapter, r)


def _wrap_chapter(res):
    from mygpo.users.models import Chapter
    user = res['key'][1]
    chapter = Chapter.wrap(res['value'])
    udb = get_userdata_database()
    chapter.set_db(udb)
    return (user, chapter)


@repeat_on_conflict(['episode_state'])
def set_episode_favorite(episode_state, is_fav):
    udb = get_userdata_database()
    episode_state.set_favorite(is_fav)
    udb.save_doc(episode_state)
