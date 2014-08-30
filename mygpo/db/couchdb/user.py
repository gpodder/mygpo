from mygpo.cache import cache_result
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb import get_userdata_database, get_single_result
from mygpo.db import QueryParameterMissing


@cache_result(timeout=60)
def get_num_listened_episodes(user):

    if not user:
        raise QueryParameterMissing('user')

    udb = get_userdata_database()
    r = udb.view('listeners/by_user_podcast',
            startkey    = [user.profile.uuid.hex, None],
            endkey      = [user.profile.uuid.hex, {}],
            reduce      = True,
            group_level = 2,
            stale       = 'update_after',
        )

    return map(_wrap_num_listened, r)


def _wrap_num_listened(obj):
    count = obj['value']
    podcast = obj['key'][1]
    return (podcast, count)


@cache_result(timeout=60)
def get_num_played_episodes(user, since=None, until={}):
    """ Number of played episodes in interval """

    if not user:
        raise QueryParameterMissing('user')

    since_str = since.strftime('%Y-%m-%d') if since else None
    until_str = until.strftime('%Y-%m-%d') if until else {}

    startkey = [user.profile.uuid.hex, since_str]
    endkey   = [user.profile.uuid.hex, until_str]

    udb = get_userdata_database()
    val = get_single_result(udb, 'listeners/by_user',
            startkey = startkey,
            endkey   = endkey,
            reduce   = True,
            stale    = 'update_after',
        )

    return val['value'] if val else 0




@cache_result(timeout=60)
def get_latest_episode_ids(user, count=10):
    """ Returns the latest episodes that the user has accessed """

    if not user:
        raise QueryParameterMissing('user')

    startkey = [user.profile.uuid.hex, {}]
    endkey   = [user.profile.uuid.hex, None]

    udb = get_userdata_database()
    res = udb.view('listeners/by_user',
            startkey     = startkey,
            endkey       = endkey,
            include_docs = True,
            descending   = True,
            limit        = count,
            reduce       = False,
            stale        = 'update_after',
        )

    return [r['value'] for r in res]



@cache_result(timeout=60)
def get_seconds_played(user, since=None, until={}):
    """ Returns the number of seconds that the user has listened

    Can be selected by timespan, podcast and episode """

    if not user:
        raise QueryParameterMissing('user')

    since_str = since.strftime('%Y-%m-%dT%H:%M:%S') if since else None
    until_str = until.strftime('%Y-%m-%dT%H:%M:%S') if until else {}

    startkey = [user.profile.uuid.hex, since_str]
    endkey   = [user.profile.uuid.hex, until_str]

    udb = get_userdata_database()
    val = get_single_result(udb, 'listeners/times_played_by_user',
            startkey = startkey,
            endkey   = endkey,
            reduce   = True,
            stale    = 'update_after',
        )

    return val['value'] if val else 0


@cache_result(timeout=60)
def user_history(user, start, length):

    if not user:
        raise QueryParameterMissing('user')

    if length <= 0:
        return []

    udb = get_userdata_database()
    res = udb.view('history/by_user',
            descending = True,
            startkey   = [user.profile.uuid.hex, {}],
            endkey     = [user.profile.uuid.hex, None],
            limit      = length,
            skip       = start,
        )

    return map(_wrap_historyentry, res)


@cache_result(timeout=60)
def device_history(user, device, start, length):

    if not user:
        raise QueryParameterMissing('user')

    if not device:
        raise QueryParameterMissing('device')

    if length <= 0:
        return []

    udb = get_userdata_database()

    res = udb.view('history/by_device',
            descending = True,
            startkey   = [user.profile.uuid.hex, device.id.hex, {}],
            endkey     = [user.profile.uuid.hex, device.id.hex, None],
            limit      = length,
            skip       = start,
        )

    return map(_wrap_historyentry, res)


def _wrap_historyentry(action):
    from mygpo.users.models import HistoryEntry
    return HistoryEntry.from_action_dict(action['value'])


@repeat_on_conflict(['state'])
def update_device_state(state, devices):
    old_devs = set(state.disabled_devices)
    state.set_device_state(devices)

    if old_devs != set(state.disabled_devices):
        udb = get_userdata_database()
        udb.save_doc(state)
