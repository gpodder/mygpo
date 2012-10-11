import hashlib

from mygpo.users.models import EpisodeUserState
from mygpo.db.couchdb.podcast import podcast_by_id
from mygpo.db.couchdb.episode import episode_for_podcast_id_url
from mygpo.couch import get_main_database
from mygpo.cache import cache_result



def episode_state_for_user_episode(user, episode):
    r = EpisodeUserState.view('episode_states/by_user_episode',
            key          = [user._id, episode._id],
            include_docs = True,
            limit        = 1,
        )

    if r:
        return r.first()

    else:
        podcast = podcast_by_id(episode.podcast)

        state = EpisodeUserState()
        state.episode = episode._id
        state.podcast = episode.podcast
        state.user = user._id
        state.ref_url = episode.url
        state.podcast_ref_url = podcast.url

        return state



def all_episode_states(episode):
    r =  EpisodeUserState.view('episode_states/by_podcast_episode',
            startkey     = [episode.podcast, episode._id, None],
            endkey       = [episode.podcast, episode._id, {}],
            include_docs = True,
        )
    return list(r)



def all_podcast_episode_states(podcast):
    r =  EpisodeUserState.view('episode_states/by_podcast_episode',
            startkey     = [podcast.get_id(), None, None],
            endkey       = [podcast.get_id(), {},   {}],
            include_docs = True
        )
    return list(r)



@cache_result(timeout=60*60)
def podcast_listener_count(episode):
    """ returns the number of users that have listened to this podcast """

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

    r = EpisodeUserState.view('listeners/by_podcast_episode',
            startkey    = [episode.get_id(), None, None],
            endkey      = [episode.get_id(), {},   {}],
            group       = True,
            group_level = 2,
            reduce      = True,
        )

    return map(_wrap_listeners)



def get_podcasts_episode_states(podcast, user_id):
    """ Returns the latest episode actions for the podcast's episodes """

    db = get_main_database()
    res = db.view('episode_states/by_user_podcast',
            startkey = [user_id, podcast.get_id(), None],
            endkey   = [user_id, podcast.get_id(), {}],
        )

    return map(lambda r: r['value'], res)



@cache_result(timeout=60*60)
def episode_listener_count(episode, start=None, end={}):
    """ returns the number of users that have listened to this episode """

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

    cache_key = 'episode-state-%s-%s-%s' % (user._id,
            hashlib.md5(podcast_url).hexdigest(),
            hashlib.md5(episode_url).hexdigest())

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
        episode = episode_for_podcast_id_url(podcast_url, episode_url,
            create=True)
        return episode_state_for_user_episode(user, episode)



def get_episode_actions(user_id, since=None, until={}, podcast_id=None,
           device_id=None):
    """ Returns Episode Actions for the given criteria"""

    since_str = since.strftime('%Y-%m-%dT%H:%M:%S') if since else None
    until_str = until.strftime('%Y-%m-%dT%H:%M:%S') if until else {}

    if since_str >= until_str:
        return

    if not podcast_id and not device_id:
        view = 'episode_actions/by_user'
        startkey = [user_id, since_str]
        endkey   = [user_id, until_str]

    elif podcast_id and not device_id:
        view = 'episode_actions/by_podcast'
        startkey = [user_id, podcast_id, since_str]
        endkey   = [user_id, podcast_id, until_str]

    elif device_id and not podcast_id:
        view = 'episode_actions/by_device'
        startkey = [user_id, device_id, since_str]
        endkey   = [user_id, device_id, until_str]

    else:
        view = 'episode_actions/by_podcast_device'
        startkey = [user_id, podcast_id, device_id, since_str]
        endkey   = [user_id, podcast_id, device_id, until_str]

    db = get_main_database()
    res = db.view(view,
            startkey = startkey,
            endkey   = endkey
        )

    return map(lambda r: r['value'], res)



@cache_result(timeout=60*60)
def episode_states_count():
    r = cls.view('episode_states/by_user_episode',
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

