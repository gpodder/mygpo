from hashlib import sha1
from datetime import datetime
from dateutil import parser

from django.core.cache import cache

from mygpo.podcasts.models import Podcast, Episode
from mygpo.users.models import EpisodeUserState
from mygpo.db import QueryParameterMissing
from mygpo.db.couchdb import get_userdata_database, get_single_result
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
    key = 'episode-state-userid-%s-episodeid-%s' % (sha1(user.profile.uuid.hex).hexdigest(),
            sha1(episode_id).hexdigest())

#   Disabled as cache invalidation does not work properly
#   state = cache.get(key)
#   if state:
#       return state

    udb = get_userdata_database()
    state = get_single_result(udb, 'episode_states/by_user_episode',
            key          = [user.profile.uuid.hex, episode_id],
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
        state.user = user.profile.uuid.hex
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


def episode_state_for_ref_urls(user, podcast_url, episode_url):

    if not user:
        raise QueryParameterMissing('user')

    if not podcast_url:
        raise QueryParameterMissing('podcast_url')

    if not episode_url:
        raise QueryParameterMissing('episode_url')


    cache_key = 'episode-state-%s-%s-%s' % (user.profile.uuid.hex,
            sha1(podcast_url).hexdigest(),
            sha1(episode_url).hexdigest())

    state = cache.get(cache_key)
    if state:
        return state

    udb = get_userdata_database()
    state = get_single_result(udb, 'episode_states/by_ref_urls',
            key   = [user.profile.uuid.hex, podcast_url, episode_url],
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
