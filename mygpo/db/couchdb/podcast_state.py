from restkit.errors import Unauthorized

from mygpo.users.models import PodcastUserState
from mygpo.users.settings import PUBLIC_SUB_PODCAST, PUBLIC_SUB_USER
from mygpo.db.couchdb import get_main_database, get_user_database
from mygpo.cache import cache_result
from mygpo.db import QueryParameterMissing
from mygpo.decorators import repeat_on_conflict


def all_podcast_states(podcast):

    if not podcast:
        raise QueryParameterMissing('podcast')

    return PodcastUserState.view('podcast_states/by_podcast',
            startkey     = [podcast.get_id(), None],
            endkey       = [podcast.get_id(), {}],
            include_docs = True,
        )


# TODO: aggregate for all users
@cache_result(timeout=60*60)
def subscribed_users(podcast):

    if not podcast:
        raise QueryParameterMissing('podcast')

    db = get_main_database()

    res = db.view('subscriptions/by_podcast',
            startkey    = [podcast.get_id(), None, None],
            endkey      = [podcast.get_id(), {}, {}],
            group       = True,
            group_level = 2,
            stale       = 'update_after',
        )

    users = (r['key'][1] for r in res)


# TODO: replace user_id with user
def subscribed_podcast_ids_by_user_id(user_id):

    if not user_id:
        raise QueryParameterMissing('user_id')

    # TODO: use user-db
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

    if not podcast:
        raise QueryParameterMissing('podcast')

    db = get_main_database()
    subscriber_sum = 0

    for podcast_id in podcast.get_ids():
        x = db.view('subscribers/by_podcast',
                startkey    = [podcast_id, None],
                endkey      = [podcast_id, {}],
                reduce      = True,
                group       = True,
                group_level = 1,
            )

        subscriber_sum += x.one()['value'] if x else 0

    return subscriber_sum


def podcast_state_for_user_podcast(user, podcast):

    if not user:
        raise QueryParameterMissing('user')

    if not podcast:
        raise QueryParameterMissing('podcast')

    db = get_user_database(user)
    r = db.view('podcast_states/by_podcast',
                key          = [podcast.get_id(), user._id],
                limit        = 1,
                include_docs = True,
                schema       = PodcastUserState,
            )

    if r:
        return r.first()

    else:
        p = PodcastUserState()
        p.podcast = podcast.get_id()
        p.user = user._id
        p.ref_url = podcast.url
        p.settings[PUBLIC_SUB_PODCAST.name]=user.get_wksetting(PUBLIC_SUB_USER)

        p.set_device_state(user.devices)

        return p


def podcast_states_for_user(user):

    if not user:
        raise QueryParameterMissing('user')

    # TODO: use user-db
    r = PodcastUserState.view('podcast_states/by_user',
            startkey     = [user._id, None],
            endkey       = [user._id, 'ZZZZ'],
            include_docs = True,
        )
    return list(r)


def podcast_states_for_device(device_id):

    if not device_id:
        raise QueryParameterMissing('device_id')

    r = PodcastUserState.view('podcast_states/by_device',
            startkey     = [device_id, None],
            endkey       = [device_id, {}],
            include_docs = True,
        )
    return list(r)


# TODO: aggregate for all users
@cache_result(timeout=60*60)
def podcast_state_count():
    r = PodcastUserState.view('podcast_states/by_user',
            limit = 0,
            stale = 'update_after',
        )
    return r.total_rows


def subscribed_podcast_ids_by_device(device):

    if not device:
        raise QueryParameterMissing('device')

    db = get_main_database()
    r = db.view('subscriptions/by_device',
            startkey = [device.id, None],
            endkey   = [device.id, {}]
        )
    return [res['key'][1] for res in r]


def subscriptions_by_user(user, public=None):
    """
    Returns a list of (podcast-id, device-id) tuples for all
    of the users subscriptions
    """

    if not user:
        raise QueryParameterMissing('user')

    # TODO: use user-db
    r = PodcastUserState.view('subscriptions/by_user',
            startkey = [user._id, public, None, None],
            endkey   = [user._id+'ZZZ', None, None, None],
            reduce   = False,
        )
    return [res['key'][1:] for res in r]


@repeat_on_conflict(['state'])
def add_subscription_action(user, state, action):
    state.add_actions([action])
    db = get_user_database(user)
    db.save_doc(state)


@repeat_on_conflict()
def add_podcast_tags(user, podcast, tags):
    state = podcast_state_for_user_podcast(user, podcast)
    state.add_tags(tags)
    db = get_user_database(user)
    db.save_doc(state)


@repeat_on_conflict()
def remove_podcast_tag(user, podcast, tag):
    state = podcast_state_for_user_podcast(user, podcast)
    tags = list(state.tags)
    if tag_str in tags:
        state.tags.remove(tag_str)
        db = get_user_database(user)
        db.save_doc(state)


@repeat_on_conflict()
def set_podcast_privacy(user, podcast, is_public):
    state = podcast_state_for_user_podcast(user, podcast)
    state.settings[PUBLIC_SUB_PODCAST.name] = is_public
    db = get_user_database(user)
    db.save_doc(state)


@repeat_on_conflict()
def subscribe_to_podcast(user, podcast, device):
    state = podcast_state_for_user_podcast(user, podcast)
    state.subscribe(device)
    try:
        db = get_user_database(user)
        db.save_doc(state)
    except Unauthorized as ex:
        raise SubscriptionException(ex)


@repeat_on_conflict()
def unsubscribe_from_podcast(user, podcast, device):
    state = podcast_state_for_user_podcast(user, podcast)
    state.unsubscribe(device)
    try:
        db = get_user_database(user)
        db.save_doc(state)
    except Unauthorized as ex:
        raise SubscriptionException(ex)


# TODO: execute this in background -- could take a while
def remove_device_from_podcast_states(user, device):
    states = podcast_states_for_device(device.id)
    for state in states:
        remove_device_from_podcast_state(user, state, dev)


@repeat_on_conflict(['state'])
def remove_device_from_podcast_state(user, state, dev):
    state.remove_device(dev)
    db = get_user_database(user)
    db.save_doc(state)


# TODO: execute this in background -- could take a while
def set_disabled_devices(user):
    podcast_states = podcast_states_for_user(user)
    for state in podcast_states:
        set_disabled_devices_for_podcast_state(user, state)


@repeat_on_conflict(['state'])
def set_disabled_devices_for_podcast_state(user, state):
    old_devs = set(state.disabled_devices)
    state.set_device_state(user.devices)

    if old_devs != set(state.disabled_devices):
        db = get_user_database(user)
        db.save_doc(state)
