from mygpo.users.models import PodcastUserState
from mygpo.couch import get_main_database
from mygpo.cache import cache_result


def all_podcast_states(podcast):
    return PodcastUserState.view('podcast_states/by_podcast',
            startkey     = [podcast.get_id(), None],
            endkey       = [podcast.get_id(), {}],
            include_docs = True,
        )


@cache_result(timeout=60*60)
def subscribed_users(podcast):
    db = get_main_database()

    res = db.view('subscriptions/by_podcast',
            startkey    = [podcast.get_id(), None, None],
            endkey      = [podcast.get_id(), {}, {}],
            group       = True,
            group_level = 2,
            stale       = 'update_after',
        )

    users = (r['key'][1] for r in res)


def subscribed_podcast_ids_by_user_id(user_id):
    subscribed = db.view('subscriptions/by_user',
            startkey    = [user_id, True, None, None],
            endkey      = [user_id, True, {}, {}],
            group       = True,
            group_level = 3,
            stale       = 'update_after',
        )
    return set(r['key'][2] for r in subscribed)


@cache_result(timeout=60*60)
def podcast_subscriber_count(podcast):
    db = get_main_database()
    subscriber_sum = 0

    for podcast_id in podcast.get_ids():
        x = db.view('subscriptions/by_podcast',
                startkey    = [podcast_id, None],
                endkey      = [podcast_id, {}],
                reduce      = True,
                group       = True,
                group_level = 2,
            )
        subscriber_sum += x.count()

    return subscriber_sum



def podcast_state_for_user_podcast(user, podcast):
    r = PodcastUserState.view('podcast_states/by_podcast',
                key          = [podcast.get_id(), user._id],
                limit        = 1,
                include_docs = True,
            )

    if r:
        return r.first()

    else:
        p = PodcastUserState()
        p.podcast = podcast.get_id()
        p.user = user._id
        p.ref_url = podcast.url
        p.settings['public_subscription'] = user.settings.get('public_subscriptions', True)

        p.set_device_state(user.devices)

        return p


def podcast_states_for_user(user):
    r = PodcastUserState.view('podcast_states/by_user',
            startkey     = [user._id, None],
            endkey       = [user._id, 'ZZZZ'],
            include_docs = True,
        )
    return list(r)


def podcast_states_for_device(device_id):
    r = PodcastUserState.view('podcast_states/by_device',
            startkey     = [device_id, None],
            endkey       = [device_id, {}],
            include_docs = True,
        )
    return list(r)


@cache_result(timeout=60*60)
def podcast_state_count():
    r = PodcastUserState.view('podcast_states/by_user',
            limit = 0,
            stale = 'update_after',
        )
    return r.total_rows


def subscribed_podcast_ids_by_device(device):
    r = self.view('subscriptions/by_device',
            startkey = [device.id, None],
            endkey   = [device.id, {}]
        )
    return [res['key'][1] for res in r]


def subscriptions_by_user(user, public=None):
    """
    Returns a list of (podcast-id, device-id) tuples for all
    of the users subscriptions
    """

    r = PodcastUserState.view('subscriptions/by_user',
            startkey = [user._id, public, None, None],
            endkey   = [user._id+'ZZZ', None, None, None],
            reduce   = False,
        )
    return [res['key'][1:] for res in r]
