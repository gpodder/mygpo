from __future__ import unicode_literals

import json
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction, IntegrityError, DataError
from django.utils.text import slugify

from mygpo.users.models import User as U, UserProfile
from mygpo.podcasts.models import (Podcast, Episode, URL, Slug, Tag,
    MergedUUID, PodcastGroup, )
from mygpo.db.couchdb.podcast_state import podcast_subscriber_count

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

    if hasattr(user, 'profile'):
        profile = user.profile
    else:
        profile = UserProfile(user=user)

    profile.uuid = u._id
    profile.suggestions_up_to_date = u.suggestions_up_to_date
    profile.about = u.about or ''
    profile.google_email = u.google_email
    profile.subscriptions_token = u.subscriptions_token
    profile.favorite_feeds_token = u.favorite_feeds_token
    profile.publisher_update_token = u.publisher_update_token
    profile.userpage_token = u.userpage_token
    profile.save()


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
