from hashlib import sha1
from datetime import datetime
from dateutil import parser

from django.core.cache import cache

from mygpo.users.models import EpisodeUserState
from mygpo.db import QueryParameterMissing
from mygpo.db.couchdb.podcast import podcast_by_id, podcast_for_url
from mygpo.db.couchdb.episode import episode_for_podcast_id_url
from mygpo.couch import get_main_database
from mygpo.cache import cache_result
from mygpo.decorators import repeat_on_conflict



def episode_state_for_user_episode(user, episode):

    if not user:
        raise QueryParameterMissing('user')

    if not episode:
        raise QueryParameterMissing('episode')


    key = 'episode-state-userid-%s-episodeid-%s' % (sha1(user._id).hexdigest(),
            sha1(episode._id).hexdigest())

    state = cache.get(key)
    if state:
        return state

    r = EpisodeUserState.view('episode_states/by_user_episode',
            key          = [user._id, episode._id],
            include_docs = True,
            limit        = 1,
        )

    if r:
        state = r.one()
        cache.set(key, state)
        return state

    else:
        podcast = podcast_by_id(episode.podcast)

        state = EpisodeUserState()
        state.episode = episode._id
        state.podcast = episode.podcast
        state.user = user._id
        state.ref_url = episode.url
        state.podcast_ref_url = podcast.url
        # don't cache here, because the state is saved by the calling function

        return state



def all_episode_states(episode):

    if not episode:
        raise QueryParameterMissing('episode')

    r =  EpisodeUserState.view('episode_states/by_podcast_episode',
            startkey     = [episode.podcast, episode._id, None],
            endkey       = [episode.podcast, episode._id, {}],
            include_docs = True,
        )
    return list(r)



def all_podcast_episode_states(podcast):

    if not podcast:
        raise QueryParameterMissing('podcast')

    r =  EpisodeUserState.view('episode_states/by_podcast_episode',
            startkey     = [podcast.get_id(), None, None],
            endkey       = [podcast.get_id(), {},   {}],
            include_docs = True
        )
    return list(r)



@cache_result(timeout=60*60)
def podcast_listener_count(episode):
    """ returns the number of users that have listened to this podcast """

    if not episode:
        raise QueryParameterMissing('episode')

    r = EpisodeUserState.view('listeners/by_podcast',
            startkey    = [episode.get_id(), None],
            endkey      = [episode.get_id(), {}],
            group       = True,
            group_level = 1,
            reduce      = True,
        )
    return r.first()['value'] if r else 0


@cache_result(timeout=60*60)
def podcast_listener_count_timespan(podcast, start=None, end={}):
    """ returns (date, listener-count) tuples for all days w/ listeners """

    if not podcast:
        raise QueryParameterMissing('podcast')

    if isinstance(start, datetime):
        start = start.isoformat()

    if isinstance(end, datetime):
        end = end.isoformat()

    r = EpisodeUserState.view('listeners/by_podcast',
            startkey    = [podcast.get_id(), start],
            endkey      = [podcast.get_id(), end],
            group       = True,
            group_level = 2,
            reduce      = True,
        )

    return map(_wrap_listener_count, r)


@cache_result(timeout=60*60)
def episode_listener_counts(episode):
    """ (Episode-Id, listener-count) tuples for episodes w/ listeners """

    if not episode:
        raise QueryParameterMissing('episode')


    r = EpisodeUserState.view('listeners/by_podcast_episode',
            startkey    = [episode.get_id(), None, None],
            endkey      = [episode.get_id(), {},   {}],
            group       = True,
            group_level = 2,
            reduce      = True,
        )

    return map(_wrap_listeners, r)



def get_podcasts_episode_states(podcast, user_id):
    """ Returns the latest episode actions for the podcast's episodes """

    if not podcast:
        raise QueryParameterMissing('podcast')

    if not user_id:
        raise QueryParameterMissing('user_id')


    db = get_main_database()
    res = db.view('episode_states/by_user_podcast',
            startkey = [user_id, podcast.get_id(), None],
            endkey   = [user_id, podcast.get_id(), {}],
        )

    return map(lambda r: r['value'], res)



@cache_result(timeout=60*60)
def episode_listener_count(episode, start=None, end={}):
    """ returns the number of users that have listened to this episode """

    if not episode:
        raise QueryParameterMissing('episode')


    r = EpisodeUserState.view('listeners/by_episode',
            startkey    = [episode._id, start],
            endkey      = [episode._id, end],
            group       = True,
            group_level = 2,
            reduce      = True,
        )
    return r.first()['value'] if r else 0



@cache_result(timeout=60*60)
def episode_listener_count_timespan(episode, start=None, end={}):
    """ returns (date, listener-count) tuples for all days w/ listeners """

    if not episode:
        raise QueryParameterMissing('episode')


    if isinstance(start, datetime):
        start = start.isoformat()

    if isinstance(end, datetime):
        end = end.isoformat()

    r = EpisodeUserState.view('listeners/by_episode',
            startkey    = [episode._id, start],
            endkey      = [episode._id, end],
            group       = True,
            group_level = 3,
            reduce      = True,
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

    res = EpisodeUserState.view('episode_states/by_ref_urls',
            key   = [user._id, podcast_url, episode_url],
            limit = 1,
            include_docs=True,
        )

    if res:
        state = res.first()
        state.ref_url = episode_url
        state.podcast_ref_url = podcast_url
        cache.set(cache_key, state, 60*60)
        return state

    else:
        podcast = podcast_for_url(podcast_url, create=True)
        episode = episode_for_podcast_id_url(podcast.get_id(), episode_url,
            create=True)
        return episode_state_for_user_episode(user, episode)



def get_episode_actions(user_id, since=None, until={}, podcast_id=None,
           device_id=None):
    """ Returns Episode Actions for the given criteria"""

    if not user_id:
        raise QueryParameterMissing('user_id')

    if since >= until:
        return []

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

    db = get_main_database()
    res = db.view(view,
            startkey = startkey,
            endkey   = endkey
        )

    return map(lambda r: r['value'], res)



@cache_result(timeout=60*60)
def episode_states_count():
    r = EpisodeUserState.view('episode_states/by_user_episode',
            limit = 0,
            stale = 'update_after',
        )
    return r.total_rows


def get_nth_episode_state(n):
    first = EpisodeUserState.view('episode_states/by_user_episode',
            skip         = n,
            include_docs = True,
            limit        = 1,
        )
    return first.one() if first else None


def get_duplicate_episode_states(user, episode):

    if not user:
        raise QueryParameterMissing('user')

    if not episode:
        raise QueryParameterMissing('episode')

    states = EpisodeUserState.view('episode_states/by_user_episode',
            key          = [user, episode],
            include_docs = True,
        )
    return list(states)


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
    db = get_main_database()

    group_level = len(filter(None, [podcast_id, episode_id, user_id]))

    r = db.view('heatmap/by_episode',
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
    state.add_actions(actions)
    state.save()
