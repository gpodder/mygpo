from hashlib import sha1
from random import random
from datetime import datetime
from collections import Counter

from restkit import RequestFailed
from couchdbkit import MultipleResultsFound

from django.core.cache import cache

from mygpo.core.models import Podcast, PodcastGroup, PodcastSubscriberData
from mygpo.core.signals import incomplete_obj
from mygpo.decorators import repeat_on_conflict
from mygpo.cache import cache_result
from mygpo.utils import get_timestamp
from mygpo.db.couchdb import get_main_database, get_userdata_database, \
    lucene_query
from mygpo.db import QueryParameterMissing
from mygpo.db.couchdb import get_main_database, get_single_result
from mygpo.db.couchdb.utils import multi_request_view, is_couchdb_id

import logging
logger = logging.getLogger(__name__)


def podcast_slugs(base_slug):
    res = Podcast.view('podcasts/by_slug',
            startkey = [base_slug, None],
            endkey   = [base_slug + 'ZZZZZ', None],
            wrap_doc = False,
        )
    return [r['key'][0] for r in res]


@cache_result(timeout=60*60)
def podcast_count():
    return Podcast.view('podcasts/by_id',
            limit = 0,
            stale = 'update_after',
        ).total_rows


@cache_result(timeout=60*60)
def podcasts_for_tag(tag):
    """ Returns the podcasts with the current tag.

    Some podcasts might be returned twice """

    if not tag:
        raise QueryParameterMissing('tag')

    res = multi_request_view(Podcast, 'podcasts/by_tag',
            wrap        = False,
            startkey    = [tag, None],
            endkey      = [tag, {}],
            reduce      = True,
            group       = True,
            group_level = 2
        )

    for r in res:
        yield (r['key'][1], r['value'])

    udb = get_userdata_database()
    res = multi_request_view(udb, 'usertags/podcasts',
            wrap        = False,
            startkey    = [tag, None],
            endkey      = [tag, {}],
            reduce      = True,
            group       = True,
            group_level = 2
        )

    for r in res:
        yield (r['key'][1], r['value'])


@cache_result(timeout=60*60)
def get_podcast_languages():
    """ Returns all 2-letter language codes that are used by podcasts.

    It filters obviously invalid strings, but does not check if any
    of these codes is contained in ISO 639. """

    from mygpo.web.utils import sanitize_language_codes

    res = Podcast.view('podcasts/by_language',
            group_level = 1,
            stale       = 'ok',
        )

    langs = [r['key'][0] for r in res]
    sane_lang = sanitize_language_codes(langs)
    sane_lang.sort()
    return sane_lang


def podcast_by_id_uncached(podcast_id, current_id=False):

    if not podcast_id:
        raise QueryParameterMissing('podcast_id')

    db = get_main_database()
    podcast = get_single_result(db, 'podcasts/by_id',
            key          = podcast_id,
            include_docs = True,
            wrapper      = _wrap_podcast_group,
        )

    if not podcast:
        return None

    if podcast.needs_update:
        incomplete_obj.send_robust(sender=podcast)

    return podcast


podcast_by_id = cache_result(timeout=60*60)(podcast_by_id_uncached)


@cache_result(timeout=60*60)
def podcastgroup_by_id(group_id):

    if not group_id:
        raise QueryParameterMissing('group_id')

    pg = PodcastGroup.get(group_id)

    if pg.needs_update:
        incomplete_obj.send_robust(sender=pg)

    return pg



@cache_result(timeout=60*60)
def podcast_for_slug(slug):

    if not slug:
        raise QueryParameterMissing('slug')

    db = get_main_database()
    obj = get_single_result(db, 'podcasts/by_slug',
            startkey     = [slug, None],
            endkey       = [slug, {}],
            include_docs = True,
            wrapper      = _wrap_podcast_group_key1,
        )

    if not obj:
        return None

    if obj.needs_update:
        incomplete_obj.send_robust(sender=obj)

    return obj


@cache_result(timeout=60*60)
def podcast_for_slug_id(slug_id):
    """ Returns the Podcast for either an CouchDB-ID for a Slug """

    if is_couchdb_id(slug_id):
        return podcast_by_id(slug_id)
    else:
        return podcast_for_slug(slug_id)


@cache_result(timeout=60*60)
def podcastgroup_for_slug_id(slug_id):
    """ Returns the Podcast for either an CouchDB-ID for a Slug """

    if not slug_id:
        raise QueryParameterMissing('slug_id')

    if is_couchdb_id(slug_id):
        return podcastgroup_by_id(slug_id)

    else:
        #TODO: implement
        return PodcastGroup.for_slug(slug_id)



def podcasts_by_id(ids):

    if ids is None:
        raise QueryParameterMissing('ids')

    if not ids:
        return []

    r = Podcast.view('podcasts/by_id',
            keys         = ids,
            include_docs = True,
            wrap_doc     = False
        )

    podcasts = map(_wrap_podcast_group, r)

    for podcast in podcasts:
        if podcast.needs_update:
            incomplete_obj.send_robust(sender=podcast)

    return podcasts


def podcasts_groups_by_id(ids):
    """ gets podcast groups and top-level podcasts for the given ids """

    if ids is None:
        raise QueryParameterMissing('ids')

    if not ids:
        return

    db = get_main_database()
    res = db.view('podcasts/podcasts_groups',
            keys         = ids,
            include_docs = True,
        )

    for r in res:
        obj = _wrap_pg(r)

        if not obj:
            yield None
            continue

        if obj.needs_update:
            incomplete_obj.send_robust(sender=obj)

        yield obj



@cache_result(timeout=60*60)
def podcast_for_oldid(oldid):

    if oldid is None:
        raise QueryParameterMissing('oldid')

    db = get_main_database()
    podcast = get_single_result(db, 'podcasts/by_oldid',
            key          = long(oldid),
            include_docs = True,
            wrapper      = _wrap_podcast_group_key1,
        )

    if not podcast:
        return None

    if podcast.needs_update:
        incomplete_obj.send_robust(sender=podcast)

    return podcast


@cache_result(timeout=60*60)
def podcastgroup_for_oldid(oldid):

    if not oldid:
        raise QueryParameterMissing('oldid')

    db = get_main_database()
    pg = get_single_result(db, 'podcasts/groups_by_oldid',
            key          = long(oldid),
            include_docs = True,
            schema       = PodcastGroup,
        )

    if not pg:
        return None

    if pg.needs_update:
        incomplete_obj.send_robust(sender=pg)

    return pg


def podcast_for_url(url, create=False):

    if not url:
        raise QueryParameterMissing('url')

    key = 'podcast-by-url-%s' % sha1(url.encode('utf-8')).hexdigest()

    podcast = cache.get(key)
    if podcast:
        return podcast

    db = get_main_database()
    podcast_group = get_single_result(db, 'podcasts/by_url',
            key          = url,
            include_docs = True,
            wrapper      = _wrap_pg,
        )

    if podcast_group:
        podcast = podcast_group.get_podcast_by_url(url)

        if podcast.needs_update:
            incomplete_obj.send_robust(sender=podcast)
        else:
            cache.set(key, podcast)

        return podcast

    if create:
        podcast = Podcast()
        podcast.created_timestamp = get_timestamp(datetime.utcnow())
        podcast.urls = [url]
        podcast.save()
        incomplete_obj.send_robust(sender=podcast)
        return podcast

    return None


def _wrap_pg(doc):

    doc = doc['doc']

    if not doc:
        return None

    if doc['doc_type'] == 'Podcast':
        return Podcast.wrap(doc)

    elif doc['doc_type'] == 'PodcastGroup':
        return PodcastGroup.wrap(doc)

    else:
        logger.error('received unknown doc_type "%s"', doc['doc_type'])


def podcast_duplicates_for_url(url):

    if not url:
        raise QueryParameterMissing('url')

    _view = 'podcasts/by_url'
    r = Podcast.view(_view,
            key          = url,
            classes      = [Podcast, PodcastGroup],
            include_docs = True,
        )

    for pg in r:
        yield pg.get_podcast_by_url(url)


def random_podcasts(language='', chunk_size=5):
    """ Returns an iterator of random podcasts

    optionaly a language code can be specified. If given the podcasts will
    be restricted to this language. chunk_size determines how many podcasts
    will be fetched at once """

    while True:
        rnd = random()
        res = Podcast.view('podcasts/random',
                startkey     = [language, rnd],
                include_docs = True,
                limit        = chunk_size,
                stale        = 'ok',
                wrap_doc     = False,
            )

        if not res:
            break

        for r in res:
            # The view podcasts/random does not include incomplete podcasts,
            # so we don't need to send any 'incomplete_obj' signals here
            yield _wrap_pg(r)


def podcasts_by_last_update(limit=100):
    res = Podcast.view('podcasts/by_last_update',
            include_docs = True,
            stale        = 'update_after',
            wrap_doc     = False,
            limit        = limit,
        )

    # TODO: this method is only used for retrieving podcasts to update;
    #       should we really send 'incomplete_obj' signals here?

    return map(_wrap_podcast_group_key1, res)


def podcasts_by_next_update(limit=100):
    """ Returns the podcasts that are due for an update next """

    res = Podcast.view('podcasts/by_next_update',
            include_docs = True,
            stale        = 'update_after',
            limit        = limit,
            classes      = [Podcast, PodcastGroup],
        )

    # TODO: this method is only used for retrieving podcasts to update;
    #       should we really send 'incomplete_obj' signals here?

    return list(res)




def all_podcasts():
    from mygpo.db.couchdb.utils import multi_request_view
    res = multi_request_view(Podcast,'podcasts/by_id',
            wrap         = False,
            include_docs = True,
            stale        = 'update_after',
        )

    # TODO: this method is only used for maintenance purposes; should we
    #       really send 'incomplete_obj' signals here?

    for r in res:
        obj = r['doc']
        if obj['doc_type'] == 'Podcast':
            yield Podcast.wrap(obj)
        else:
            pid = r[u'key']
            pg = PodcastGroup.wrap(obj)
            podcast = pg.get_podcast_by_id(pid)
            yield podcast


def podcasts_to_dict(ids, use_cache=False):

    if ids is None:
        raise QueryParameterMissing('ids')

    if not ids:
        return dict()


    ids = list(set(ids))
    objs = dict()

    cache_objs = []
    if use_cache:
        res = cache.get_many(ids)
        cache_objs.extend(res.values())
        ids = [x for x in ids if x not in res.keys()]

    db_objs = podcasts_by_id(ids)

    for obj in (cache_objs + db_objs):

        # get_multi returns dict {'key': _id, 'error': 'not found'}
        # for non-existing objects
        if isinstance(obj, dict) and 'error' in obj:
            _id = obj['key']
            objs[_id] = None
            continue

        for i in obj.get_ids():
            objs[i] = obj

    if use_cache:
        cache.set_many(dict( (obj.get_id(), obj) for obj in db_objs))

    return objs



def podcasts_need_update(limit=100):
    db = get_main_database()
    res = db.view('episodes/need_update',
            group_level = 1,
            reduce      = True,
            limit       = limit,
        )

    # TODO: this method is only used for retrieving podcasts to update;
    #       should we really send 'incomplete_obj' signals here?

    for r in res:
        podcast_id = r['key']
        podcast = podcast_by_id(podcast_id)
        if podcast:
            yield podcast


@cache_result(timeout=60*60)
def get_flattr_podcasts(offset=0, limit=20):
    """ returns all podcasts that contain Flattr payment URLs """

    r = Podcast.view('podcasts/flattr',
            skip         = offset,
            limit        = limit,
            classes      = [Podcast, PodcastGroup],
            include_docs = True,
            reduce       = False,
        )

    podcasts = list(r)

    for podcast in podcasts:
        if podcast.needs_update:
            incomplete_obj.send_robust(sender=podcast)

    return podcasts


@cache_result(timeout=60*60)
def get_flattr_podcast_count():
    """ returns the number of podcasts that contain Flattr payment URLs """
    db = get_main_database()
    r = get_single_result(db, 'podcasts/flattr')
    return r['value']


@cache_result(timeout=60*60)
def get_license_podcasts(offset=0, limit=20, license_url=None):
    """ returns a page of podcasts w/ license information """

    kwargs = {}
    if license_url:
        kwargs['key'] = license_url

    r = Podcast.view('podcasts/license',
            skip = offset,
            limit = limit,
            classes = [Podcast, PodcastGroup],
            include_docs = True,
            reduce = False,
            **kwargs
    )

    podcasts = list(r)

    for podcast in podcasts:
        if podcast.needs_update:
            incomplete_obj.send_robust(sender=podcast)

    return podcasts


@cache_result(timeout=60*60)
def get_license_podcast_count(license_url=None):
    """ returns the number of podcasts that contain license information """

    kwargs = {}
    if license_url:
        kwargs['key'] = license_url

    db = get_main_database()
    r = get_single_result(db, 'podcasts/license', **kwargs)

    return r['value'] if r else 0


@cache_result(timeout=60*60)
def get_podcast_licenses():
    """ returns the licenses that are assigned to podcasts """
    db = get_main_database()
    r = db.view('podcasts/license',
            reduce = True,
            group_level = 1,
    )

    return Counter({ x['key']: x['value'] for x in r })


def subscriberdata_for_podcast(podcast_id):

    if not podcast_id:
        raise QueryParameterMissing('podcast_id')

    db = get_main_database()
    data = get_single_result(db, 'podcasts/subscriber_data',
            key          = podcast_id,
            include_docs = True,
            schema       = PodcastSubscriberData,
        )

    if not data:
        data = PodcastSubscriberData()
        data.podcast = podcast_id

    return data



def _wrap_podcast_group(res):
    if res['doc']['doc_type'] == 'Podcast':
        return Podcast.wrap(res['doc'])
    else:
        pg = PodcastGroup.wrap(res['doc'])
        id = res['key']
        return pg.get_podcast_by_id(id)


def _wrap_podcast_group_key1(res):
    obj = res['doc']
    if obj['doc_type'] == 'Podcast':
        return Podcast.wrap(obj)

    else:
        pid = res[u'key'][1]
        pg = PodcastGroup.wrap(obj)
        podcast = pg.get_podcast_by_id(pid)
        return podcast



def search_wrapper(result):
    doc = result['doc']
    if doc['doc_type'] == 'Podcast':
        p = Podcast.wrap(doc)
    elif doc['doc_type'] == 'PodcastGroup':
        p = PodcastGroup.wrap(doc)
    p._id = result['id']
    return p


@cache_result(timeout=60*60)
def search(q, offset=0, num_results=20):

    if not q:
        return [], 0

    db = get_main_database()

    FIELDS = ['title', 'description']
    q = lucene_query(FIELDS, q)

    try:
        res = db.search('podcasts/search',
                wrapper      = search_wrapper,
                include_docs = True,
                limit        = num_results,
                stale        = 'update_after',
                skip         = offset,
                q            = q,
            )

        podcasts = list(res)

        for podcast in podcasts:
            if podcast.needs_update:
                incomplete_obj.send_robust(sender=podcast)

        return podcasts, res.total_rows

    except RequestFailed:
        return [], 0


def reload_podcast(podcast):
    return podcast_by_id_uncached(podcast.get_id())


@repeat_on_conflict(['podcast'], reload_f=reload_podcast)
def update_additional_data(podcast, twitter):
    podcast.twitter = twitter
    podcast.save()

    # clear the whole cache until we have a better invalidation mechanism
    cache.clear()


@repeat_on_conflict(['podcast'], reload_f=reload_podcast)
def update_related_podcasts(podcast, related):
    if podcast.related_podcasts == related:
        return

    podcast.related_podcasts = related
    podcast.save()


@repeat_on_conflict(['podcast'], reload_f=reload_podcast)
def delete_podcast(podcast):
    podcast.delete()
