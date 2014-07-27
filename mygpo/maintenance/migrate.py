from __future__ import unicode_literals

import json
from datetime import datetime

from django.contrib.auth.models import User

from mygpo.users.models import User as U, UserProfile, Client, SyncGroup
from mygpo.podcasts.models import Podcast
from mygpo.publisher.models import PublishedPodcast

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


def migrate_user(u):

    # no need in migrating already deleted users
    if u.deleted:
        return

    user, created = User.objects.update_or_create(username=u.username,
        defaults = {
            'email': u.email,
            'is_active': u.is_active,
            'is_staff': u.is_staff,
            'is_superuser': u.is_superuser,
            'last_login': u.last_login or datetime(1970, 01, 01),
            'date_joined': u.date_joined,
            'password': u.password,
        }
    )

    profile = user.profile
    profile.uuid = u._id
    profile.suggestions_up_to_date = u.suggestions_up_to_date
    profile.about = u.about or ''
    profile.google_email = u.google_email
    profile.subscriptions_token = u.subscriptions_token
    profile.favorite_feeds_token = u.favorite_feeds_token
    profile.publisher_update_token = u.publisher_update_token
    profile.userpage_token = u.userpage_token
    profile.twitter = to_maxlength(UserProfile, 'twitter', u.twitter) if u.twitter is not None else None
    profile.activation_key = u.activation_key
    profile.settings = json.dumps(u.settings)
    profile.save()

    for podcast_id in u.published_objects:
        try:
            podcast = Podcast.objects.all().get_by_any_id(podcast_id)
        except Podcast.DoesNotExist:
            logger.warn("Podcast with ID '%s' does not exist", podcast_id)
            continue

        PublishedPodcast.objects.get_or_create(publisher=user, podcast=podcast)

    for device in u.devices:
        client = Client.objects.get_or_create(user=user,
                                              uid=device.uid,
            defaults = {
                'id': device.id,
                'name': device.name,
                'type': device.type,
                'deleted': device.deleted,
                'user_agent': device.user_agent,
            }
        )

    logger.info('Migrading %d sync groups', len(getattr(u, 'sync_groups', [])))
    groups = list(SyncGroup.objects.filter(user=user))
    for group_ids in getattr(u, 'sync_groups', []):
        try:
            group = groups.pop()
        except IndexError:
            group = SyncGroup.objects.create(user=user)

        # remove all clients from the group
        Client.objects.filter(sync_group=group).update(sync_group=None)

        for client_id in group_ids:
            client = Client.objects.get(id=client_id)
            assert client.user == user
            client.sync_group = group
            client.save()

    SyncGroup.objects.filter(pk__in=[g.pk for g in groups]).delete()


from couchdbkit import Database
db = Database('http://127.0.0.1:6984/mygpo_users')
from couchdbkit.changes import ChangesStream, fold, foreach


MIGRATIONS = {
    'User': (U, migrate_user),
    'Suggestions': (None, None),
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
