from datetime import datetime
import collections

from django.db import transaction

from mygpo.users.models import Client
from mygpo.subscriptions.models import (Subscription, SubscribedPodcast,
    PodcastConfig, )
from mygpo.subscriptions.signals import subscription_changed
from mygpo.history.models import HistoryEntry
from mygpo.utils import to_maxlength

import logging
logger = logging.getLogger(__name__)


SUBSCRIPTION_ACTIONS = (
    HistoryEntry.SUBSCRIBE,
    HistoryEntry.UNSUBSCRIBE,
)

@transaction.atomic
def subscribe(podcast, user, client, ref_url=None):
    """ subscribes user to the current podcast on one client """

    ref_url = ref_url or podcast.url
    now = datetime.utcnow()

    subscription, created = Subscription.objects.get_or_create(
        user=user, client=client, podcast=podcast, defaults={
            'ref_url': to_maxlength(Subscription, 'ref_url', ref_url),
            'created': now,
            'modified': now,
        }
    )

    if not created:
        return

    logger.info('{user} subscribed to {podcast} on {client}'.format(
        user=user, podcast=podcast, client=client))

    HistoryEntry.objects.create(
        timestamp=now,
        podcast=podcast,
        user=user,
        client=client,
        action=HistoryEntry.SUBSCRIBE,
    )

    subscription_changed.send(sender=podcast, user=user,
                              client=client, subscribed=True)


@transaction.atomic
def unsubscribe(podcast, user, client):
    """ unsubscribes user from the current podcast on one client """
    now = datetime.utcnow()

    try:
        subscription = Subscription.objects.get(
            user=user,
            client=client,
            podcast=podcast,
        )
    except Subscription.DoesNotExist:
        return

    subscription.delete()

    logger.info('{user} unsubscribed from {podcast} on {client}'.format(
        user=user, podcast=podcast, client=client))

    HistoryEntry.objects.create(
        timestamp=now,
        podcast=podcast,
        user=user,
        client=client,
        action=HistoryEntry.UNSUBSCRIBE,
    )

    subscription_changed.send(sender=podcast, user=user,
                              client=client, subscribed=False)


@transaction.atomic
def subscribe_all(podcast, user, ref_url=None):
    """ subscribes user to the current podcast on all clients """
    clients = user.client_set.all()
    for client in clients:
        subscribe(podcast, user, client, ref_url)


@transaction.atomic
def unsubscribe_all(podcast, user):
    """ unsubscribes user from the current podcast on all clients """
    now = datetime.utcnow()

    clients = user.client_set.filter(subscription__podcast=podcast)
    for client in clients:
        unsubscribe(podcast, user, client)


def get_subscribe_targets(podcast, user):
    """ Clients / SyncGroup on which the podcast can be subscribed

    This excludes all devices/syncgroups on which the podcast is already
    subscribed """

    clients = Client.objects.filter(user=user)\
                            .exclude(subscription__podcast=podcast)\
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
    private = PodcastConfig.objects.get_private_podcasts(user)

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

    history = HistoryEntry.objects.filter(user=user)\
                                  .filter(action__in=SUBSCRIPTION_ACTIONS)\
                                  .order_by('timestamp')

    if client:
        history = history.filter(client=client)

    if since:
        history = history.filter(timestamp__gt=since)

    if until:
        history = history.filter(timestamp__lte=since)

    if public_only:
        private = PodcastConfig.objects.get_private_podcasts(user)
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

    subscribe = [podcast for (podcast, value) in subscriptions if value > 0]
    unsubscribe = [podcast for (podcast, value) in subscriptions if value < 0]

    return subscribe, unsubscribe
