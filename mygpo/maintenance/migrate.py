from __future__ import unicode_literals

from mygpo.core.models import Podcast as P, Episode as E
from django.contrib.contenttypes.models import ContentType
from django.db import transaction, IntegrityError
from django.utils.text import slugify
import json
from datetime import datetime
from mygpo.podcasts.models import Podcast, Episode, URL, Slug, Tag, MergedUUID

import logging
logger = logging.getLogger(__name__)
#p = P.wrap(json.load(open('tmp.txt')))


def migrate_episode(e):

    podcast, created = Podcast.objects.get_or_create(id=e.podcast, defaults={
        'created': datetime.utcnow(),
    })

    if created:
        logger.info('Created stub for podcast %s', e.podcast)

    e2, created = Episode.objects.update_or_create(id=e._id, defaults = {
        'title': e.title or '',
        'guid': e.guid,
        'description': e.description or '',
        'subtitle': e.subtitle or '',
        'content': e.content or '',
        'link': e.link,
        'released': e.released,
        'author': e.author,
        'duration': max(0, e.duration) if e.duration is not None else None,
        'filesize': max(0, e.filesize) if e.filesize is not None else None,
        'language': e.language[:10] if e.language is not None else None,
        'last_update': e.last_update,
        'outdated': e.outdated,
        'mimetypes': ','.join(e.mimetypes),
        'listeners': max(0, e.listeners) if e.listeners is not None else None,
        'content_types': ','.join(e.content_types),
        'flattr_url': e.flattr_url,
        'created': datetime.fromtimestamp(e.created_timestamp) if e.created_timestamp else datetime.utcnow(),
        'license': e.license,
        'podcast': podcast,
    })

    update_urls(e, e2, None)
    update_slugs(e, e2, None)
    update_ids(e, e2)



def migrate_podcast(p):
    logger.info('Migrating podcast %r', p)
    import time
    time.sleep(5)

    p2, created = Podcast.objects.update_or_create(id=p._id, defaults = {
        'title': p.title or '',
        'subtitle': p.subtitle or '',
        'description': p.description or '',
        'link': p.link,
        'language': p.language,
        'created': datetime.fromtimestamp(p.created_timestamp) if p.created_timestamp else datetime.utcnow(),
        'last_update': p.last_update,
        'license': p.license,
        'flattr_url': p.flattr_url,
        'outdated': p.outdated,
        'author': p.author,
        'logo_url': p.logo_url,
        'common_episode_title': p.common_episode_title or '',
        'new_location': p.new_location,
        'latest_episode_timestamp': p.latest_episode_timestamp,
        'episode_count': p.episode_count or 0,
        'hub': p.hub,
        'content_types': ','.join(p.content_types),
        'restrictions': ','.join(p.restrictions),
        'twitter': getattr(p, 'twitter', None),
    })

    update_urls(p, p2, None)
    update_slugs(p, p2, None)
    update_tags(p, p2)
    update_ids(p, p2)

    time.sleep(10)
    return p2


@transaction.atomic
def update_urls(old, new, scope):

    existing_urls = {u.url: u for u in new.urls.all()}
    for n, url in enumerate(old.urls):
        try:
            u = existing_urls.pop(url)
            u.order = n
            u.save()
        except KeyError:
            try:
                URL.objects.create(url=url, content_object=new, order=n, scope=scope)
            except IntegrityError as ie:
                logger.warn('Could not create URL for %s: %s', new, ie)

    delete = [u.pk for u in existing_urls]

    logger.info('Deleting %d URLs', len(delete))
    URL.objects.filter(id__in=delete).delete()


@transaction.atomic
def update_slugs(old, new, scope):

    existing_slugs = {s.slug: s for s in new.slugs.all()}
    logger.info('%d existing slugs', len(existing_slugs))

    new_slugs = filter(None, [old.slug] + old.merged_slugs + [old.oldid] + old.merged_oldids)
    new_slugs = map(unicode, new_slugs)
    new_slugs = map(slugify, new_slugs)
    logger.info('%d new slugs', len(new_slugs))

    max_length = Slug._meta.get_field('slug').max_length

    max_order = max([s.order for s in existing_slugs.values()] + [len(new_slugs)])
    logger.info('Renumbering slugs starting from %d', max_order)
    for n, slug in enumerate(existing_slugs.values(), max_order+1):
        slug.order = n
        slug.save()

    logger.info('%d existing slugs', len(existing_slugs))

    for n, slug in enumerate(new_slugs):
        try:
            s = existing_slugs.pop(slug)
            logger.info('Updating new slug %d: %s', n, slug)
            s.order = n
            s.save()
        except KeyError:
            logger.info('Creating new slug %d: %s', n, slug)
            try:
                Slug.objects.create(slug=slug[:max_length], content_object=new,
                                    order=n, scope=scope)
            except IntegrityError as ie:
                logger.warn('Could not create Slug for %s: %s', new, ie)



    delete = [s.pk for s in existing_slugs.values()]
    Slug.objects.filter(id__in=delete).delete()


@transaction.atomic
def update_tags(old, new):
    # TODO: delete?
    for tag in old.tags.get('feed', []):
        t, created = Tag.objects.get_or_create(
            tag=tag,
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


def migrate(since=592054):
    with ChangesStream(db,
                       feed="continuous",
                       heartbeat=True,
                       include_docs=True,
                       since=since,
                    ) as stream:
        for change in stream:
            migrate_change(change)
