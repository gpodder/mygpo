from restkit.errors import Unauthorized

from mygpo.users.models import PodcastUserState, SubscriptionException
from mygpo.users.settings import PUBLIC_SUB_PODCAST, PUBLIC_SUB_USER
from mygpo.db.couchdb import get_userdata_database, get_single_result
from mygpo.cache import cache_result
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


@cache_result(timeout=60*60)
def subscribed_users(podcast):

    if not podcast:
        raise QueryParameterMissing('podcast')

    udb = get_userdata_database()

    res = udb.view('subscriptions/by_podcast',
            startkey    = [podcast.get_id(), None, None],
            endkey      = [podcast.get_id(), {}, {}],
            group       = True,
            group_level = 2,
            stale       = 'update_after',
        )

    users = (r['key'][1] for r in res)
    return users


def subscribed_podcast_ids_by_user_id(user_id):

    if not user_id:
        raise QueryParameterMissing('user_id')

    udb = get_userdata_database()

    subscribed = udb.view('subscriptions/by_user',
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

    udb = get_userdata_database()
    subscriber_sum = 0

    for podcast_id in podcast.get_ids():
        x = get_single_result(udb, 'subscribers/by_podcast',
                startkey    = [podcast_id, None],
                endkey      = [podcast_id, {}],
                reduce      = True,
                group       = True,
                group_level = 1,
            )

        subscriber_sum += x['value'] if x else 0

    return subscriber_sum


def podcast_state_for_user_podcast(user, podcast):

    if not user:
        raise QueryParameterMissing('user')

    if not podcast:
        raise QueryParameterMissing('podcast')

    udb = get_userdata_database()

    p = get_single_result(udb, 'podcast_states/by_podcast',
                key          = [podcast.get_id(), user.profile.uuid.hex],
                limit        = 1,
                include_docs = True,
                schema       = PodcastUserState,
            )

    if not p:
        p = PodcastUserState()
        p.podcast = podcast.get_id()
        p.user = user.profile.uuid.hex
        p.ref_url = podcast.url
        p.settings[PUBLIC_SUB_PODCAST.name]=user.profile.get_wksetting(PUBLIC_SUB_USER)

        p.set_device_state(user.client_set.all())

    return p


def podcast_states_for_user(user):

    if not user:
        raise QueryParameterMissing('user')

    udb = get_userdata_database()

    r = udb.view('podcast_states/by_user',
            startkey     = [user.profile.uuid.hex, None],
            endkey       = [user.profile.uuid.hex, 'ZZZZ'],
            include_docs = True,
            schema       = PodcastUserState,
        )

    states = list(r)
    for state in states:
        state.set_db(udb)

    return states


def podcast_states_for_device(device_id):

    if not device_id:
        raise QueryParameterMissing('device_id')

    udb = get_userdata_database()

    r = udb.view('podcast_states/by_device',
            startkey     = [device_id, None],
            endkey       = [device_id, {}],
            include_docs = True,
            schema       = PodcastUserState,
        )

    states = list(r)

    for state in states:
        state.set_db(udb)

    return states


@cache_result(timeout=60*60)
def podcast_state_count():
    udb = get_userdata_database()
    r = udb.view('podcast_states/by_user',
            limit = 0,
            stale = 'update_after',
        )
    return r.total_rows


def subscribed_podcast_ids_by_device(device):

    if not device:
        raise QueryParameterMissing('device')

    udb = get_userdata_database()
    r = udb.view('subscriptions/by_device',
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

    udb = get_userdata_database()

    r = udb.view('subscriptions/by_user',
            startkey = [user.profile.uuid.hex, public, None, None],
            endkey   = [user.profile.uuid.hex+'ZZZ', None, None, None],
            reduce   = False,
            schema   = PodcastUserState,
        )
    return [res['key'][1:] for res in r]


@repeat_on_conflict(['state'])
def add_subscription_action(state, action):
    udb = get_userdata_database()
    state.add_actions([action])
    udb.save_doc(state)


@repeat_on_conflict(['state'])
def delete_podcast_state(state):
    udb = get_userdata_database()
    udb.delete_doc(state)


@repeat_on_conflict(['state'])
def add_podcast_tags(state, tags):
    udb = get_userdata_database()
    state.add_tags(tags)
    udb.save_doc(state)

@repeat_on_conflict(['state'])
def remove_podcast_tags(state, tag_str):
    if tag_str not in state.tags:
        return
    udb = get_userdata_database()
    state.tags.remove(tag_str)
    udb.save_doc(state)


@repeat_on_conflict(['state'])
def set_podcast_privacy_settings(state, is_public):
    udb = get_userdata_database()
    state.settings[PUBLIC_SUB_PODCAST.name] = is_public
    udb.save_doc(state)


@repeat_on_conflict(['state'])
def remove_device_from_podcast_state(state, dev):
    udb = get_userdata_database()
    state.remove_device(dev)
    udb.save_doc(state)

@repeat_on_conflict(['state'])
def subscribe_on_device(state, device):
    state.subscribe(device)
    udb = get_userdata_database()
    udb.save_doc(state)

@repeat_on_conflict(['state'])
def unsubscribe_on_device(state, device):
    state.unsubscribe(device)
    udb = get_userdata_database()
    udb.save_doc(state)


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


def get_subscribed_podcast_states_by_device(device):
    udb = get_userdata_database()
    r = udb.view('subscriptions/by_device',
            startkey     = [device.id, None],
            endkey       = [device.id, {}],
            include_docs = True,
            schema       = PodcastUserState,
        )

    states = list(r)

    for state in states:
        state.set_db(udb)

    return states


def get_subscribed_podcast_states_by_user(user_id, public=None):
    """
    Returns the Ids of all subscribed podcasts
    """

    udb = get_userdata_database()
    r = udb.view('subscriptions/by_user',
            startkey     = [user_id, public, None, None],
            endkey       = [user_id, {}, {}, {}],
            reduce       = False,
            include_docs = True,
            schema       = PodcastUserState,
        )

    states = list(r)

    for state in states:
        state.set_db(udb)

    return states


@repeat_on_conflict()
def subscribe(podcast, user, device):
    """ subscribes user to the current podcast on one or more devices """
    from mygpo.core.signals import subscription_changed
    state = podcast_state_for_user_podcast(user, podcast)

    # accept devices, and also lists and tuples of devices
    devices = device if isinstance(device, (list, tuple)) else [device]

    for device in devices:

        try:
            subscribe_on_device(state, device)
            subscription_changed.send(sender=podcast, user=user,
                                      device=device, subscribed=True)
        except Unauthorized as ex:
            raise SubscriptionException(ex)


@repeat_on_conflict()
def unsubscribe(podcast, user, device):
    """ unsubscribes user from the current podcast on one or more devices """
    from mygpo.core.signals import subscription_changed
    state = podcast_state_for_user_podcast(user, podcast)

    # accept devices, and also lists and tuples of devices
    devices = device if isinstance(device, (list, tuple)) else [device]

    for device in devices:

        try:
            unsubscribe_on_device(state, device)
            subscription_changed.send(sender=podcast, user=user, device=device,
                                      subscribed=False)
        except Unauthorized as ex:
            raise SubscriptionException(ex)
