from collections import Counter

from couchdbkit import ResourceNotFound

from mygpo.cache import cache_result
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb import get_main_database, get_user_database
from mygpo.users.settings import FLATTR_TOKEN, FLATTR_AUTO, FLATTR_MYGPO, \
         FLATTR_USERNAME
from mygpo.db import QueryParameterMissing
from mygpo.db.couchdb.episode import episodes_by_id


@cache_result(timeout=60)
def get_num_listened_episodes(user):

    if not user:
        raise QueryParameterMissing('user')

    # TODO: use user-db
    db = get_main_database()
    r = db.view('listeners/by_user_podcast',
            startkey    = [user._id, None],
            endkey      = [user._id, {}],
            reduce      = True,
            group_level = 2,
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

    startkey = [user._id, since_str]
    endkey   = [user._id, until_str]

    # TODO: use user-db
    db = get_main_database()
    res = db.view('listeners/by_user',
            startkey = startkey,
            endkey   = endkey,
            reduce   = True,
        )

    val = res.one()
    return val['value'] if val else 0




@cache_result(timeout=60)
def get_latest_episodes(user, count=10):
    """ Returns the latest episodes that the user has accessed """

    if not user:
        raise QueryParameterMissing('user')

    startkey = [user._id, {}]
    endkey   = [user._id, None]

    # TODO: use user-db
    db = get_main_database()
    res = db.view('listeners/by_user',
            startkey     = startkey,
            endkey       = endkey,
            include_docs = True,
            descending   = True,
            limit        = count,
            reduce       = False,
        )

    keys = [r['value'] for r in res]
    return episodes_by_id(keys)



@cache_result(timeout=60)
def get_seconds_played(user, since=None, until={}):
    """ Returns the number of seconds that the user has listened

    Can be selected by timespan, podcast and episode """

    if not user:
        raise QueryParameterMissing('user')

    since_str = since.strftime('%Y-%m-%dT%H:%M:%S') if since else None
    until_str = until.strftime('%Y-%m-%dT%H:%M:%S') if until else {}

    startkey = [user._id, since_str]
    endkey   = [user._id, until_str]

    # TODO: use user-db
    db = get_main_database()
    res = db.view('listeners/times_played_by_user',
            startkey = startkey,
            endkey   = endkey,
            reduce   = True,
        )

    val = res.one()
    return val['value'] if val else 0



@cache_result(timeout=60*60)
def suggestions_for_user(user):

    if not user:
        raise QueryParameterMissing('user')

    db = get_user_database(user)
    from mygpo.users.models import Suggestions
    r = db.view('suggestions/by_user',
                key          = user._id,
                include_docs = True,
                schema = Suggestions
            )

    if r:
        return r.first()

    else:
        s = Suggestions()
        s.user = user._id
        return s


def update_suggestions(user, suggestions_obj, suggested_ids):
    """ Updates the suggested podcasts for the given suggestions object """
    db = get_user_database(user)
    suggestions_obj.podcasts = suggested_ids
    db.save_doc(suggestions_obj, batch='ok')


@repeat_on_conflict(['suggestions_obj'])
def append_to_suggestions_blacklist(user, podcast):
    db = get_user_database(user)
    suggestions_obj = suggestions_for_user(user)
    blacklisted = list(set(suggestions_obj.blacklist + [podcast.get_id()]))
    suggestions_obj.blacklist = blacklisted
    db.save_doc(suggestions_obj, batch='ok')


@cache_result(timeout=60*60)
def user_agent_stats():
    # TODO: check
    from mygpo.users.models import User
    res = User.view('clients/by_ua_string',
        wrap_doc    = False,
        group_level = 1,
        stale       = 'update_after',
    )

    return Counter(dict((r['key'], r['value']) for r in res))


def deleted_users():
    #TODO: check
    from mygpo.users.models import User
    users = User.view('users/deleted',
            include_docs = True,
            reduce       = False,
        )
    return list(users)


def deleted_user_count():
    #TODO: check
    from mygpo.users.models import User
    total = User.view('users/deleted',
            reduce = True,
        )
    return list(total)[0]['value'] if total else 0



@cache_result(timeout=60)
def user_history(user, start, length):

    if not user:
        raise QueryParameterMissing('user')

    if length <= 0:
        return []

    #TODO: use user-db
    db = get_main_database()
    res = db.view('history/by_user',
            descending = True,
            startkey   = [user._id, {}],
            endkey     = [user._id, None],
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

    #TODO: use user-db
    db = get_main_database()

    res = db.view('history/by_device',
            descending = True,
            startkey   = [user._id, device.id, {}],
            endkey     = [user._id, device.id, None],
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

    # TODO: use user-db
    user.save()


def _wrap_historyentry(action):
    from mygpo.users.models import HistoryEntry
    return HistoryEntry.from_action_dict(action['value'])


def user_by_google_email(email):
    """ Get a user by its connected Google account """

    from mygpo.users.models import User
    users = User.view('users/by_google_email',
            key          = email,
            include_docs = True,
        )

    if not users:
        return None

    return users.one()


@repeat_on_conflict(['user'])
def set_users_google_email(user, email):
    """ Update the Google accoutn connected with the user """

    if user.google_email == email:
        return user

    user.google_email = email
    user.save()
    return user


def get_user_by_id(user_id):
    from mygpo.users.models import User
    try:
        return User.get(user_id)
    except ResourceNotFound:
        return None
