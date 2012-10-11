from mygpo.cache import cache_result
from mygpo.counter import Counter
from mygpo.couch import get_main_database
from mygpo.db.couchdb.episode import episodes_by_id


@cache_result(timeout=60)
def get_num_listened_episodes(user):
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
def get_num_played_episodes(self, since=None, until={}):
    """ Number of played episodes in interval """

    since_str = since.strftime('%Y-%m-%d') if since else None
    until_str = until.strftime('%Y-%m-%d') if until else {}

    startkey = [self._id, since_str]
    endkey   = [self._id, until_str]

    db = get_main_database()
    res = db.view('listeners/by_user',
            startkey = startkey,
            endkey   = endkey,
            reduce   = True,
        )

    val = res.one()
    return val['value'] if val else 0




@cache_result(timeout=60)
def get_latest_episodes(self, count=10):
    """ Returns the latest episodes that the user has accessed """

    startkey = [self._id, {}]
    endkey   = [self._id, None]

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
def get_seconds_played(self, since=None, until={}):
    """ Returns the number of seconds that the user has listened

    Can be selected by timespan, podcast and episode """

    since_str = since.strftime('%Y-%m-%dT%H:%M:%S') if since else None
    until_str = until.strftime('%Y-%m-%dT%H:%M:%S') if until else {}

    startkey = [self._id, since_str]
    endkey   = [self._id, until_str]

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
    from mygpo.users.models import Suggestions
    r = Suggestions.view('suggestions/by_user',
                key          = user._id,
                include_docs = True,
            )

    if r:
        return r.first()

    else:
        s = Suggestions()
        s.user = user._id
        return s


@cache_result(timeout=60*60)
def user_agent_stats():
    res = User.view('clients/by_ua_string',
        wrap_doc    = False,
        group_level = 1,
        stale       = 'update_after',
    )

    return Counter(dict((r['key'], r['value']) for r in res))


def deleted_users():
    users = User.view('users/deleted',
            include_docs = True,
            reduce       = False,
        )
    return list(users)


def deleted_user_count():
    total = User.view('users/deleted',
            reduce = True,
        )
    return list(total)[0]['value'] if total else 0



@cache_result(timeout=60)
def user_history(user, start, length):
    db = get_main_database()
    res = db.view('history/by_user',
            descending = True,
            startkey   = [user._id, None],
            endkey     = [user._id, {}],
            limit      = length,
            skip       = start,
        )

    return map(_wrap_historyentry, res)


@cache_result(timeout=60)
def device_history(user, device, start, length):
    db = get_main_database()

    res = self._db.view('history/by_device',
            descending = True,
            startkey   = [user._id, device.id, None],
            endkey     = [user._id, device.id, {}],
            limit      = length,
            skip       = start,
        )

    return map(_wrap_historyentry, res)


def _wrap_historyentry(action):
    return HistoryEntry.from_action_dict(action['action'])
