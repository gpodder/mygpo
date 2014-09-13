from datetime import datetime

from django.db import transaction

from mygpo.subscriptions.models import Subscription
from mygpo.subscriptions.signals import subscription_changed
from mygpo.history.models import HistoryEntry
from mygpo.utils import to_maxlength
from mygpo.celery import celery

import logging
logger = logging.getLogger(__name__)


@celery.task(max_retries=5, default_retry_delay=60)
def subscribe(podcast, user, client, ref_url=None):
    """ subscribes user to the current podcast on one client

    Takes syned devices into account. """
    ref_url = ref_url or podcast.url
    now = datetime.utcnow()
    clients = _affected_clients(client)

    # fully execute subscriptions, before firing events
    changed = list(_perform_subscribe(podcast, user, clients, now, ref_url))
    _fire_events(podcast, user, changed, True)


@celery.task(max_retries=5, default_retry_delay=60)
def unsubscribe(podcast, user, client):
    """ unsubscribes user from the current podcast on one client

    Takes syned devices into account. """
    now = datetime.utcnow()
    clients = _affected_clients(client)

    # fully execute unsubscriptions, before firing events
    # otherwise the first fired event might revert the unsubscribe
    changed = list(_perform_unsubscribe(podcast, user, clients, now))
    _fire_events(podcast, user, changed, False)


@celery.task(max_retries=5, default_retry_delay=60)
def subscribe_all(podcast, user, ref_url=None):
    """ subscribes user to the current podcast on all clients """
    ref_url = ref_url or podcast.url
    now = datetime.utcnow()
    clients = user.client_set.all()

    # fully execute subscriptions, before firing events
    changed = list(_perform_subscribe(podcast, user, clients, now, ref_url))
    _fire_events(podcast, user, changed, True)


@celery.task(max_retries=5, default_retry_delay=60)
def unsubscribe_all(podcast, user):
    """ unsubscribes user from the current podcast on all clients """
    now = datetime.utcnow()
    clients = user.client_set.filter(subscription__podcast=podcast)

    # fully execute subscriptions, before firing events
    changed = list(_perform_unsubscribe(podcast, user, clients, now))
    _fire_events(podcast, user, changed, False)


@transaction.atomic
def _perform_subscribe(podcast, user, clients, timestamp, ref_url):
    """ Subscribes to a podcast on multiple clients

    Yields the clients on which a subscription was added, ie not those where
    the subscription already existed. """

    for client in clients:
        subscription, created = Subscription.objects.get_or_create(
            user=user, client=client, podcast=podcast, defaults={
                'ref_url': to_maxlength(Subscription, 'ref_url', ref_url),
                'created': timestamp,
                'modified': timestamp,
            }
        )

        if not created:
            continue

        logger.info('{user} subscribed to {podcast} on {client}'.format(
            user=user, podcast=podcast, client=client))

        HistoryEntry.objects.create(
            timestamp=timestamp,
            podcast=podcast,
            user=user,
            client=client,
            action=HistoryEntry.SUBSCRIBE,
        )

        yield client


@transaction.atomic
def _perform_unsubscribe(podcast, user, clients, timestamp):
    """ Unsubscribes from a podcast on multiple clients

    Yields the clients on which a subscription was removed, ie not those where
    the podcast was not subscribed. """

    for client in clients:

        try:
            subscription = Subscription.objects.get(
                user=user,
                client=client,
                podcast=podcast,
            )
        except Subscription.DoesNotExist:
            continue

        subscription.delete()

        logger.info('{user} unsubscribed from {podcast} on {client}'.format(
            user=user, podcast=podcast, client=client))

        HistoryEntry.objects.create(
            timestamp=timestamp,
            podcast=podcast,
            user=user,
            client=client,
            action=HistoryEntry.UNSUBSCRIBE,
        )

        yield client


def _affected_clients(client):
    """ the clients that are affected if the given one is to be changed """
    if client.sync_group:
        # if the client is synced, all are affected
        return client.sync_group.client_set.all()

    else:
        # if its not synced, only the client is affected
        return [client]


def _fire_events(podcast, user, clients, subscribed):
    """ Fire the events for subscription / unsubscription """
    for client in clients:
        subscription_changed.send(sender=podcast.__class__, instance=podcast,
                                  user=user, client=client,
                                  subscribed=subscribed)
