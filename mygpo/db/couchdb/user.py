from mygpo.cache import cache_result
from mygpo.db.couchdb import get_userdata_database, get_single_result
from mygpo.db import QueryParameterMissing


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
