from __future__ import unicode_literals

import json
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from mygpo.podcasts.models import Tag
from mygpo.users.models import UserProfile, Client, SyncGroup, PodcastUserState
from mygpo.subscriptions.models import Subscription, PodcastConfig
from mygpo.history.models import HistoryEntry
from mygpo.podcasts.models import Podcast

import logging
logger = logging.getLogger(__name__)


def to_maxlength(cls, field, val):
    """ Cut val to the maximum length of cls's field """
    max_length = cls._meta.get_field(field).max_length
    orig_length = len(val)
    if orig_length > max_length:
        val = val[:max_length]
        logger.warn('%s.%s length reduced from %d to %d',
                    cls.__name__, field, orig_length, max_length)

    return val


def migrate_pstate(state):
    """ migrate a podcast state """

    try:
        user = User.objects.get(profile__uuid=state.user)
    except User.DoesNotExist:
        logger.warn("User with ID '{id}' does not exist".format(
            id=state.user))
        return

    try:
        podcast = Podcast.objects.all().get_by_any_id(state.podcast)
    except Podcast.DoesNotExist:
        logger.warn("Podcast with ID '{id}' does not exist".format(
            id=state.podcast))
        return

    logger.info('Updating podcast state for user {user} and podcast {podcast}'
                .format(user=user, podcast=podcast))

    # move all tags
    for tag in state.tags:
        ctype = ContentType.objects.get_for_model(podcast)
        tag, created = Tag.objects.get_or_create(tag=tag,
                                                 source=Tag.USER,
                                                 user=user,
                                                 content_type=ctype,
                                                 object_id=podcast.id
                                                 )
        if created:
            logger.info("Created tag '{}' for user {} and podcast {}",
                        tag, user, podcast)

    # create all history entries
    history = HistoryEntry.objects.filter(user=user, podcast=podcast)
    for action in state.actions:
        timestamp = action.timestamp
        try:
            client = user.client_set.get(id=action.device)
        except Client.DoesNotExist:
            logger.warn("Client '{cid}' does not exist; skipping".format(
                cid=action.device))
            continue
        action = action.action
        he_data = {
            'timestamp': timestamp,
            'podcast': podcast,
            'user': user,
            'client': client,
            'action': action,
        }
        he, created = HistoryEntry.objects.get_or_create(**he_data)

        if created:
            logger.info('History Entry created: {user} {action} {podcast} '
                        'on {client} @ {timestamp}'.format(**he_data))

    # check which clients are currently subscribed
    subscribed_devices = get_subscribed_devices(state)
    subscribed_ids = subscribed_devices.keys()
    subscribed_clients = user.client_set.filter(id__in=subscribed_ids)
    unsubscribed_clients = user.client_set.exclude(id__in=subscribed_ids)

    # create subscriptions for subscribed clients
    for client in subscribed_clients:
        ts = subscribed_devices[client.id.hex]
        sub_data = {
            'user': user,
            'client': client,
            'podcast': podcast,
        }
        defaults = {
            'ref_url': state.ref_url,
            'created': ts,
            'modified': ts,
            'deleted': client.id.hex in state.disabled_devices,
        }
        subscription, created = Subscription.objects.get_or_create(
            defaults, **sub_data)

        if created:
            sub_data.update(defaults)
            logger.info('Subscription created: {user} subscribed to {podcast} '
                'on {client} @ {created}'.format(**sub_data))

        else:
            subscription.modified = ts
            subscription.deleted = client.id.hex in state.disabled_devices
            subscription.ref_url = state.ref_url
            subscription.save()

    # delete all other subscriptions
    Subscription.objects.filter(user=user, podcast=podcast,
                                client__in=unsubscribed_clients).delete()

    # only create the PodcastConfig obj if there are any settings
    if state.settings:
        logger.info('Updating {num} settings'.format(num=len(state.settings)))
        PodcastConfig.objects.update_or_create(user=user, podcast=podcast,
            defaults = {
                'settings': json.dumps(state.settings),
            }
        )


def get_subscribed_devices(state):
    """ device Ids on which the user subscribed to the podcast """
    devices = {}

    for action in state.actions:
        if action.action == "subscribe":
            if not action.device in state.disabled_devices:
                devices[action.device] = action.timestamp
        else:
            if action.device in devices:
                devices.pop(action.device)

    return devices



from couchdbkit import Database
db = Database('http://127.0.0.1:6984/mygpo_userdata_copy')
from couchdbkit.changes import ChangesStream, fold, foreach


MIGRATIONS = {
    'PodcastUserState': (PodcastUserState, migrate_pstate),
    'User': (None, None),
    'Suggestions': (None, None),
    'EpisodeUserState': (None, None),
}

def migrate_change(c):
    logger.info('Migrate seq %s', c['seq'])
    doc = c['doc']

    if not 'doc_type' in doc:
        logger.warn('Document contains no doc_type: %r', doc)
        return

    doctype = doc['doc_type']

    cls, migrate = MIGRATIONS[doctype]

    if cls is None:
        logger.warn("Skipping '%s'", doctype)
        return

    obj = cls.wrap(doc)
    migrate(obj)


def migrate(since=0):
    with ChangesStream(db,
                       feed="continuous",
                       heartbeat=True,
                       include_docs=True,
                       since=since,
                    ) as stream:
        for change in stream:
            migrate_change(change)
