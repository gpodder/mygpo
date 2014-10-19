from __future__ import unicode_literals

import json
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db import reset_queries

from mygpo.podcasts.models import Tag
from mygpo.users.models import EpisodeUserState, Client
from mygpo.chapters.models import Chapter
from mygpo.subscriptions.models import Subscription, PodcastConfig
from mygpo.podcastlists.models import PodcastList, PodcastListEntry
from mygpo.history.models import EpisodeHistoryEntry
from mygpo.podcasts.models import Episode, Podcast, PodcastGroup
from mygpo.directory.models import Category as C
from mygpo.categories.models import Category, CategoryEntry, CategoryTag
from mygpo.favorites.models import FavoriteEpisode
from mygpo.votes.models import Vote

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


#class EpisodeUserState(Document, SettingsMixin):
#    ref_url       = StringProperty(required=True)
#    podcast_ref_url = StringProperty(required=True)


def migrate_estate(state):
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

    try:
        episode = Episode.objects.filter(podcast=podcast).get_by_any_id(state.episode)
    except Episode.DoesNotExist:
        logger.warn("Episode with ID '{id}' does not exist".format(
            id=state.episode))
        return

    logger.info('Migrating episode state ({id}) for user {user} and episode {episode}'
                .format(id=state._id, user=user, episode=episode))

    for action in state.actions:
        migrate_eaction(user, episode, state, action)


def migrate_eaction(user, episode, state, ea):

    logger.info('Migrating {action} action'.format(action=ea.action))

    if ea.device is None:
        client = None

    else:
        try:
            client = user.client_set.get(id=ea.device)
        except Client.DoesNotExist:
            logger.warn("Client '{cid}' does not exist; skipping".format(
                cid=ea.device))
            return

    created = datetime.utcfromtimestamp(ea.upload_timestamp) if ea.upload_timestamp else datetime.utcnow()
    entry, created = EpisodeHistoryEntry.objects.get_or_create(
        user=user,
        client=client,
        episode=episode,
        action=ea.action,
        timestamp=ea.timestamp,
        defaults = {
            'created': created,
            'started': ea.started,
            'stopped': ea.playmark,
            'total': ea.total,
            'podcast_ref_url': state.podcast_ref_url,
            'episode_ref_url': state.ref_url,
        },
    )

    if created:
        logger.info('Episode History Entry created: {user} {action} {episode}'
                    'on {client} @ {timestamp}'.format(user=user,
                        action=entry.action, episode=episode, client=client,
                        timestamp=entry.timestamp))


def migrate_category(cat):

    logger.info('Migrating category {category}'.format(category=cat))
    category, created = Category.objects.get_or_create(
        title=to_maxlength(Category, 'title', cat.label)
    )

    for spelling in cat.spellings + [cat.label]:
        s, c = CategoryTag.objects.get_or_create(
            tag=slugify(to_maxlength(CategoryTag, 'tag', spelling.strip())),
            defaults={
                'category': category,
            }
        )

    for podcast_id in cat.podcasts:
        if isinstance(podcast_id, dict):
            podcast_id = podcast_id['podcast']
        logger.info(repr(podcast_id))

        try:
            podcast = Podcast.objects.all().get_by_any_id(podcast_id)
        except Podcast.DoesNotExist:
            logger.warn("Podcast with ID '{podcast_id}' does not exist".format(
                podcast_id=podcast_id))
            continue

        entry, c = CategoryEntry.objects.get_or_create(category=category,
                                                       podcast=podcast)

    category.save()


from couchdbkit import Database
db = Database('http://127.0.0.1:5984/mygpo_userdata_copy')
from couchdbkit.changes import ChangesStream, fold, foreach


MIGRATIONS = {
    'PodcastUserState': (None, None),
    'User': (None, None),
    'Suggestions': (None, None),
    'EpisodeUserState': (EpisodeUserState, migrate_estate),
    'PodcastList': (None, None),
    'Category': (C, migrate_category),
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
    reset_queries()


def migrate(since=0, db=db):
    with ChangesStream(db,
                       feed="continuous",
                       heartbeat=True,
                       include_docs=True,
                       since=since,
                    ) as stream:
        for change in stream:
            migrate_change(change)
