from collections import Counter

from couchdbkit import ResourceNotFound

from django.db.models import Count
from django.contrib.auth import get_user_model

from mygpo.cache import cache_result
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb import get_userdata_database, \
    get_single_result, get_suggestions_database
from mygpo.users.settings import FLATTR_TOKEN, FLATTR_AUTO, FLATTR_MYGPO, \
         FLATTR_USERNAME
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



@cache_result(timeout=60*60)
def suggestions_for_user(user):

    if not user:
        raise QueryParameterMissing('user')

    from mygpo.users.models import Suggestions
    sdb = get_suggestions_database()
    s = get_single_result(sdb, 'suggestions/by_user',
                key          = user.profile.uuid.hex,
                include_docs = True,
                schema       = Suggestions,
            )

    if not s:
        s = Suggestions()
        s.user = user.profile.uuid.hex

    return s


@repeat_on_conflict(['suggestions'])
def update_suggestions(suggestions, podcast_ids):
    """ Updates the suggestions object with new suggested podcasts """

    if suggestions.podcasts == podcast_ids:
        return

    sdb = get_suggestions_database()
    suggestions.podcasts = podcast_ids
    sdb.save_doc(suggestions)


@repeat_on_conflict(['suggestions'])
def blacklist_suggested_podcast(suggestions, podcast_id):
    """ Adds a podcast to the list of unwanted suggestions """

    if podcast_id in suggestions.blacklist:
        return

    sdb = get_suggestions_database()
    suggestions.blacklist.append(podcast_id)
    sdb.save_doc(suggestions)


@cache_result(timeout=60*60)
def user_agent_stats():
    from mygpo.users.models import Client
    result = Client.objects.values('user_agent').annotate(Count('user_agent'))
    return Counter({x['user_agent']: x['user_agent__count'] for x in result})


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
            startkey   = [user.profile.uuid.hex, device.id, {}],
            endkey     = [user.profile.uuid.hex, device.id, None],
            limit      = length,
            skip       = start,
        )

    return map(_wrap_historyentry, res)


@repeat_on_conflict(['user'])
def update_flattr_settings(user, token, enabled=None, flattr_mygpo=False,
        username=None):
    """ Updates the Flattr settings of a user """

    if enabled is not None:
        user.settings[FLATTR_AUTO.name] = enabled

    if token is not None:
        user.settings[FLATTR_TOKEN.name] = token

    if flattr_mygpo is not None:
        user.settings[FLATTR_MYGPO.name] = flattr_mygpo

    if username is not None:
        user.settings[FLATTR_USERNAME.name] = username

    user.save()


def _wrap_historyentry(action):
    from mygpo.users.models import HistoryEntry
    return HistoryEntry.from_action_dict(action['value'])


def user_by_google_email(email):
    """ Get a user by its connected Google account """
    User = get_user_model()
    try:
        return User.objects.get(profile__google_email=email)
    except User.DoesNotExist:
        return None


@repeat_on_conflict(['user'])
def set_users_google_email(user, email):
    """ Update the Google accoutn connected with the user """

    if user.google_email == email:
        return user

    user.google_email = email
    user.save()
    return user


def get_user_by_id(user_id):
    User = get_user_model()
    try:
        User.objects.get(profile__uuid=user_id)
    except User.DoesNotExist:
        return None


@repeat_on_conflict(['user'])
def activate_user(user):
    """ activates a user so that he is able to login """
    user.is_active = True
    user.activation_key = None
    user.save()


@repeat_on_conflict(['user'])
def set_device_deleted(user, device, is_deleted):
    device.deleted = is_deleted
    user.set_device(device)
    user.save()


@repeat_on_conflict(['state'])
def update_device_state(state, devices):
    old_devs = set(state.disabled_devices)
    state.set_device_state(devices)

    if old_devs != set(state.disabled_devices):
        udb = get_userdata_database()
        udb.save_doc(state)


@repeat_on_conflict(['user'])
def unsync_device(user, device):
    if user.is_synced(device):
        user.unsync_device(device)
        user.save()


@repeat_on_conflict(['user'])
def set_device(user, device):
    user.set_device(device)
    user.save()


@repeat_on_conflict(['user'])
def create_missing_user_tokens(user):

    generated = False

    from mygpo.users.models import TOKEN_NAMES
    for tn in TOKEN_NAMES:
        if getattr(user, tn) is None:
            user.create_new_token(tn)
            generated = True

    if generated:
        user.save()

@repeat_on_conflict(['user'])
def add_published_objs(user, ids):
    """ Adds published objects to the user """
    user.published_objects = list(set(user.published_objects + list(ids)))
    user.save()
