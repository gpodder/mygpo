from __future__ import unicode_literals

from mygpo.core.models import Podcast as P, Episode as E, PodcastGroup as G
from django.contrib.contenttypes.models import ContentType
from django.db import transaction, IntegrityError
from django.utils.text import slugify
import json
from datetime import datetime
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


def migrate_episode(e):

    podcast, created = Podcast.objects.get_or_create(id=e.podcast)

    if created:
        logger.info('Created stub for podcast %s', e.podcast)

    e2, created = Episode.objects.update_or_create(id=e._id, defaults = {
        'title': e.title or '',
        'subtitle': e.subtitle or '',
        'guid': to_maxlength(Episode, 'guid', e.guid) if e.guid is not None else None,
        'description': e.description or '',
        'content': e.content or '',
        'link': e.link,
        'released': e.released,
        'author': e.author,
        'duration': max(0, e.duration) if e.duration is not None else None,
        'filesize': max(0, e.filesize) if e.filesize is not None else None,
        'language': to_maxlength(Episode, 'language', e.language) if e.language is not None else None,
        'last_update': e.last_update,
        'outdated': e.outdated,
        'mimetypes': to_maxlength(Episode, 'mimetypes', ','.join(e.mimetypes)),
        'listeners': max(0, e.listeners) if e.listeners is not None else None,
        'content_types': ','.join(e.content_types),
        'flattr_url': to_maxlength(Episode, 'flattr_url', e.flattr_url) if e.flattr_url else None,
        'created': datetime.fromtimestamp(e.created_timestamp) if e.created_timestamp else datetime.utcnow(),
        'license': e.license,
        'podcast': podcast,
    })

    update_urls(e, e2)
    update_slugs(e, e2)
    update_ids(e, e2)



def migrate_podcast(p):
    logger.info('Migrating podcast %r', p)

    if p.group_member_name:
        pid = p.id
    else:
        pid = p._id

    p2, created = Podcast.objects.update_or_create(id=pid, defaults = {
        'title': p.title or '',
        'subtitle': p.subtitle or '',
        'description': p.description or '',
        'link': p.link,
        'language': to_maxlength(Podcast, 'language', p.language) if p.language is not None else None,
        'created': datetime.fromtimestamp(p.created_timestamp) if p.created_timestamp else datetime.utcnow(),
        'last_update': p.last_update,
        'license': p.license,
        'flattr_url': to_maxlength(Podcast, 'flattr_url', p.flattr_url) if p.flattr_url else None,
        'outdated': p.outdated,
        'author': p.author,
        'logo_url': p.logo_url,
        'common_episode_title': to_maxlength(Podcast, 'common_episode_title', p.common_episode_title or ''),
        'new_location': p.new_location,
        'latest_episode_timestamp': p.latest_episode_timestamp,
        'episode_count': p.episode_count or 0,
        'hub': p.hub,
        'content_types': ','.join(p.content_types),
        'restrictions': ','.join(p.restrictions),
        'twitter': getattr(p, 'twitter', None),
        'group_member_name': p.group_member_name,
        'update_interval': p.update_interval,
        'subscribers': podcast_subscriber_count(p),
    })

    update_urls(p, p2)
    update_slugs(p, p2)
    update_tags(p, p2)
    update_ids(p, p2)

    return p2


def migrate_podcastgroup(g):
    logger.info('Migrating podcast group %r', g)

    g2, created = PodcastGroup.objects.update_or_create(id=g._id, defaults = {
        'title': g.title,
    })

    for p in g.podcasts:
        p2 = migrate_podcast(p)
        p2.group = g2
        p2.save()

    update_slugs(g, g2)

    return g2



def update_urls(old, new):

    existing_urls = {u.url: u for u in new.urls.all()}
    logger.info('%d existing URLs', len(existing_urls))

    new_urls = old.urls
    logger.info('%d new URLs', len(new_urls))

    with transaction.atomic():
        max_order = max([s.order for s in existing_urls.values()] + [len(new_urls)])
        logger.info('Renumbering URLs starting from %d', max_order)
        for n, url in enumerate(existing_urls.values(), max_order+1):
            url.order = n
            url.save()

    logger.info('%d existing URLs', len(existing_urls))
    for n, url in enumerate(new_urls):
        try:
            u = existing_urls.pop(url)
            u.order = n
            u.save()
        except KeyError:
            try:
                URL.objects.create(url=to_maxlength(URL, 'url', url),
                                   content_object=new,
                                   order=n,
                                   scope=new.scope,
                                )
            except IntegrityError as ie:
                logger.warn('Could not create URL for %s: %s', new, ie)

    with transaction.atomic():
        delete = [u.pk for u in existing_urls.values()]
        logger.info('Deleting %d URLs', len(delete))
        URL.objects.filter(id__in=delete).delete()


def update_slugs(old, new):
    new_slugs = filter(None, [old.slug] + old.merged_slugs +
                             [old.oldid] + old.merged_oldids)
    new_slugs = map(unicode, new_slugs)
    new_slugs = map(slugify, new_slugs)
    new_slugs = map(lambda s: to_maxlength(Slug, 'slug', s), new_slugs)
    new.set_slugs(new_slugs)


@transaction.atomic
def update_tags(old, new):
    # TODO: delete?
    for tag in old.tags.get('feed', []):
        t, created = Tag.objects.get_or_create(
            tag=to_maxlength(Tag, 'tag', unicode(tag)),
            source=Tag.FEED,
            content_type=ContentType.objects.get_for_model(new),
            object_id=new.pk,
        )


@transaction.atomic
def update_ids(old, new):
    # TODO: delete?
    for mid in old.merged_ids:
        u, created = MergedUUID.objects.get_or_create(
            uuid = mid,
            content_type=ContentType.objects.get_for_model(new),
            object_id=new.pk,
        )


from couchdbkit import Database
db = Database('http://127.0.0.1:6984/mygpo_core_copy')
from couchdbkit.changes import ChangesStream, fold, foreach


MIGRATIONS = {
    'Podcast': (P, migrate_podcast),
    'Episode': (E, migrate_episode),
    'PodcastGroup': (G, migrate_podcastgroup),
    'PodcastList': (None, None),
    'PodcastSubscriberData': (None, None),
    'EmailMessage': (None, None),
    'ExamplePodcasts': (None, None),
}

def migrate_change(c):
    logger.info('Migrate seq %s', c['seq'])
    doctype = c['doc']['doc_type']

    cls, migrate = MIGRATIONS[doctype]

    if cls is None:
        return

    obj = cls.wrap(c['doc'])
    migrate(obj)


def migrate(since=1187918):
    with ChangesStream(db,
                       feed="continuous",
                       heartbeat=True,
                       include_docs=True,
                       since=since,
                    ) as stream:
        for change in stream:
            migrate_change(change)
