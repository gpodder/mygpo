from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import transaction
from celery import shared_task

from mygpo.subscriptions.models import Subscription
from mygpo.subscriptions.signals import subscription_changed
from mygpo.history.models import HistoryEntry
from mygpo.podcasts.models import Podcast
from mygpo.utils import to_maxlength

import logging

logger = logging.getLogger(__name__)


@shared_task(max_retries=5, default_retry_delay=60)
def subscribe(podcast_pk, user_pk, client_uid, ref_url=None):
    """subscribes user to the current podcast on one client

    Takes syned devices into account."""
    podcast = Podcast.objects.get(pk=podcast_pk)

    User = get_user_model()
    user = User.objects.get(pk=user_pk)

    client = user.client_set.get(uid=client_uid)

    ref_url = ref_url or podcast.url
    now = datetime.utcnow()
    clients = _affected_clients(client)

    # fully execute subscriptions, before firing events
    changed = list(_perform_subscribe(podcast, user, clients, now, ref_url))
    _fire_events(podcast, user, changed, True)


@shared_task(max_retries=5, default_retry_delay=60)
def unsubscribe(podcast_pk, user_pk, client_uid):
    """unsubscribes user from the current podcast on one client

    Takes syned devices into account."""
    podcast = Podcast.objects.get(pk=podcast_pk)

    User = get_user_model()
    user = User.objects.get(pk=user_pk)

    client = user.client_set.get(uid=client_uid)

    now = datetime.utcnow()
    clients = _affected_clients(client)

    # fully execute unsubscriptions, before firing events
    # otherwise the first fired event might revert the unsubscribe
    changed = list(_perform_unsubscribe(podcast, user, clients, now))
    _fire_events(podcast, user, changed, False)


@shared_task(max_retries=5, default_retry_delay=60)
def subscribe_all(podcast_pk, user_pk, ref_url=None):
    """subscribes user to the current podcast on all clients"""
    podcast = Podcast.objects.get(pk=podcast_pk)

    User = get_user_model()
    user = User.objects.get(pk=user_pk)

    ref_url = ref_url or podcast.url
    now = datetime.utcnow()
    clients = user.client_set.all()

    # fully execute subscriptions, before firing events
    changed = list(_perform_subscribe(podcast, user, clients, now, ref_url))
    _fire_events(podcast, user, changed, True)


@shared_task(max_retries=5, default_retry_delay=60)
def unsubscribe_all(podcast_pk, user_pk):
    """unsubscribes user from the current podcast on all clients"""
    podcast = Podcast.objects.get(pk=podcast_pk)

    User = get_user_model()
    user = User.objects.get(pk=user_pk)

    now = datetime.utcnow()
    clients = user.client_set.filter(subscription__podcast=podcast)

    # fully execute subscriptions, before firing events
    changed = list(_perform_unsubscribe(podcast, user, clients, now))
    _fire_events(podcast, user, changed, False)


@transaction.atomic
def _perform_subscribe(podcast, user, clients, timestamp, ref_url):
    """Subscribes to a podcast on multiple clients

    Yields the clients on which a subscription was added, ie not those where
    the subscription already existed."""

    for client in clients:
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            client=client,
            podcast=podcast,
            defaults={
                "ref_url": to_maxlength(Subscription, "ref_url", ref_url),
                "created": timestamp,
                "modified": timestamp,
            },
        )

        if not created:
            continue

        logger.info(
            "{user} subscribed to {podcast} on {client}".format(
                user=user, podcast=podcast, client=client
            )
        )

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
    """Unsubscribes from a podcast on multiple clients

    Yields the clients on which a subscription was removed, ie not those where
    the podcast was not subscribed."""

    for client in clients:

        try:
            subscription = Subscription.objects.get(
                user=user, client=client, podcast=podcast
            )
        except Subscription.DoesNotExist:
            continue

        subscription.delete()

        logger.info(
            "{user} unsubscribed from {podcast} on {client}".format(
                user=user, podcast=podcast, client=client
            )
        )

        HistoryEntry.objects.create(
            timestamp=timestamp,
            podcast=podcast,
            user=user,
            client=client,
            action=HistoryEntry.UNSUBSCRIBE,
        )

        yield client


def _affected_clients(client):
    """the clients that are affected if the given one is to be changed"""
    if client.sync_group:
        # if the client is synced, all are affected
        return client.sync_group.client_set.all()

    else:
        # if its not synced, only the client is affected
        return [client]


def _fire_events(podcast, user, clients, subscribed):
    """Fire the events for subscription / unsubscription"""
    for client in clients:
        subscription_changed.send(
            sender=podcast.__class__,
            instance=podcast,
            user=user,
            client=client,
            subscribed=subscribed,
        )
