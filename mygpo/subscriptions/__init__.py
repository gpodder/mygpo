import collections

from mygpo.users.models import Client
from mygpo.usersettings.models import UserSettings
from mygpo.subscriptions.models import Subscription, SubscribedPodcast
from mygpo.history.models import SUBSCRIPTION_ACTIONS, HistoryEntry

import logging
logger = logging.getLogger(__name__)

# we cannot import models in __init__.py, because it gets loaded while all
# apps are loaded; ideally all these methods would be moved into a different
# (non-__init__) module


def get_subscribe_targets(podcast, user):
    """ Clients / SyncGroup on which the podcast can be subscribed

    This excludes all devices/syncgroups on which the podcast is already
    subscribed """

    clients = Client.objects.filter(user=user)\
                            .exclude(subscription__podcast=podcast,
                                     subscription__user=user)\
                            .select_related('sync_group')

    targets = set()
    for client in clients:
        if client.sync_group:
            targets.add(client.sync_group)
        else:
            targets.add(client)

    return targets


def get_subscribed_podcasts(user, only_public=False):
    """ Returns all subscribed podcasts for the user

    The attribute "url" contains the URL that was used when subscribing to
    the podcast """

    subscriptions = Subscription.objects.filter(user=user)\
                                        .order_by('podcast')\
                                        .distinct('podcast')\
                                        .select_related('podcast')
    private = UserSettings.objects.get_private_podcasts(user)

    podcasts = []
    for subscription in subscriptions:
        podcast = subscription.podcast
        public = subscription.podcast not in private

        # check if we want to include this podcast
        if only_public and not public:
            continue

        subpodcast = SubscribedPodcast(podcast, public, subscription.ref_url)
        podcasts.append(subpodcast)

    return podcasts


def get_subscription_history(user, client=None, since=None, until=None,
                             public_only=False):
    """ Returns chronologically ordered subscription history entries

    Setting device_id restricts the actions to a certain device
    """

    logger.info('Subscription History for {user}'.format(user=user.username))
    history = HistoryEntry.objects.filter(user=user)\
                                  .filter(action__in=SUBSCRIPTION_ACTIONS)\
                                  .order_by('timestamp')

    if client:
        logger.info(u'... client {client_uid}'.format(client_uid=client.uid))
        history = history.filter(client=client)

    if since:
        logger.info('... since {since}'.format(since=since))
        history = history.filter(timestamp__gt=since)

    if until:
        logger.info('... until {until}'.format(until=until))
        history = history.filter(timestamp__lte=until)

    if public_only:
        logger.info('... only public')
        private = UserSettings.objects.get_private_podcasts(user)
        history = history.exclude(podcast__in=private)

    return history


def get_subscription_change_history(history):
    """ Actions that added/removed podcasts from the subscription list

    Returns an iterator of all subscription actions that either
     * added subscribed a podcast that hasn't been subscribed directly
       before the action (but could have been subscribed) earlier
     * removed a subscription of the podcast is not longer subscribed
       after the action

    This method assumes, that no subscriptions exist at the beginning of
    ``history``.
    """

    subscriptions = collections.defaultdict(int)

    for entry in history:
        if entry.action == HistoryEntry.SUBSCRIBE:
            subscriptions[entry.podcast] += 1

            # a new subscription has been added
            if subscriptions[entry.podcast] == 1:
                yield entry

        elif entry.action == HistoryEntry.UNSUBSCRIBE:
            subscriptions[entry.podcast] -= 1

            # the last subscription has been removed
            if subscriptions[entry.podcast] == 0:
                yield entry


def subscription_diff(history):
    """ Calculates a diff of subscriptions based on a history (sub/unsub) """

    subscriptions = collections.defaultdict(int)

    for entry in history:
        if entry.action == HistoryEntry.SUBSCRIBE:
            subscriptions[entry.podcast] += 1

        elif entry.action == HistoryEntry.UNSUBSCRIBE:
            subscriptions[entry.podcast] -= 1

    subscribe = [podcast for (podcast, value) in
                 subscriptions.items() if value > 0]
    unsubscribe = [podcast for (podcast, value) in
                   subscriptions.items() if value < 0]

    return subscribe, unsubscribe
