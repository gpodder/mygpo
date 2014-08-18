from mygpo.users.models import PodcastUserState
from mygpo.db.couchdb import get_userdata_database
from mygpo.db import QueryParameterMissing
from mygpo.decorators import repeat_on_conflict


def all_podcast_states(podcast):

    if not podcast:
        raise QueryParameterMissing('podcast')

    udb = get_userdata_database()

    r = udb.view('podcast_states/by_podcast',
            startkey     = [podcast.get_id(), None],
            endkey       = [podcast.get_id(), {}],
            include_docs = True,
            schema       = PodcastUserState,
        )

    states = list(r)

    for state in states:
        state.set_db(udb)

    return states


@repeat_on_conflict(['state'])
def delete_podcast_state(state):
    udb = get_userdata_database()
    udb.delete_doc(state)


@repeat_on_conflict(['state'])
def update_podcast_state_podcast(state, new_id, new_url):
    state.ref_url = new_url
    state.podcast = new_id
    udb = get_userdata_database()
    udb.save_doc(state)


@repeat_on_conflict(['state'])
def merge_podcast_states(state, state2):
    # overwrite settings in state2 with state's settings
    settings = state2.settings
    settings.update(state.settings)
    state.settings = settings


    disabled_devices = state.disabled_devices + state2.disabled_devices
    disabled_devices = filter(None, set(disabled_devices))
    state.disabled_devices = disabled_devices

    merged_ids = state.merged_ids + [state2._id] + state2.merged_ids
    merged_ids = set(filter(None, merged_ids))
    merged_ids = list(merged_ids - set([state._id]))
    state.merged_ids = merged_ids

    tags = state.tags + state2.tags
    tags = filter(None, set(tags))
    state.tags = tags

    udb = get_userdata_database()
    udb.save_doc(state)
