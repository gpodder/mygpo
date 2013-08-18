from itertools import chain
from operator import itemgetter
from collections import Counter

from couchdbkit import ResourceConflict

from mygpo.cel import celery
from mygpo.db.couchdb.user import suggestions_for_user, update_device_state


@celery.task(max_retries=5, default_retry_delay=60)
def sync_user(user):
    """ Syncs all of the user's device groups """

    for group in user.get_grouped_devices():
        if group.is_synced:
            device = group.devices[0]
            user.sync_group(device)


@celery.task(max_retries=5, default_retry_delay=60)
def update_suggestions(user, max_suggestions=15):
    """ updates the suggestions of a user """

    # get suggestions object
    suggestion = suggestions_for_user(user)

    # calculate possible suggestions
    subscribed_podcasts = list(set(user.get_subscribed_podcasts()))
    subscribed_podcasts = filter(None, subscribed_podcasts)
    related = chain.from_iterable([p.related_podcasts for p in subscribed_podcasts])

    # filter out blacklisted podcasts
    related = filter(lambda pid: not pid in suggestion.blacklist, related)

    # get most relevant
    counter = Counter(related)
    get_podcast_id = itemgetter(0)
    suggested = map(get_podcast_id, counter.most_common(max_suggestions))
    suggestion.podcasts = suggested

    try:
        # update suggestions object
        suggestion.save()

    except ResourceConflict as ex:
        raise update_suggestions.retry(exc=ex)


@celery.task(max_retries=5, default_retry_delay=60)
def set_device_task_state(user):
    """ updates the device states of a user in all his/her podcast states """
    from mygpo.db.couchdb.podcast_state import podcast_states_for_user
    podcast_states = podcast_states_for_user(user)
    for state in podcast_states:
        update_device_state(state, user.devices)
