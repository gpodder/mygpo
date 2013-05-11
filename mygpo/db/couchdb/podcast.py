from hashlib import sha1
from random import random
from datetime import datetime

from restkit import RequestFailed

from django.core.cache import cache

from mygpo.core.models import Podcast, PodcastGroup, PodcastSubscriberData
from mygpo.core.signals import incomplete_obj
from mygpo.decorators import repeat_on_conflict
from mygpo.cache import cache_result
from mygpo.utils import get_timestamp
from mygpo.db.couchdb import get_main_database
from mygpo.db import QueryParameterMissing
from mygpo.db.couchdb.utils import multi_request_view, is_couchdb_id


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

    res = multi_request_view(Podcast, 'usertags/podcasts',
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


@cache_result(timeout=60*60)
def podcast_by_id(podcast_id, current_id=False):

    if not podcast_id:
        raise QueryParameterMissing('podcast_id')

    r = Podcast.view('podcasts/by_id',
            key          = podcast_id,
            classes      = [Podcast, PodcastGroup],
            include_docs = True,
        )

    if not r:
        return None

    podcast_group = r.first()

    podcast = podcast_group.get_podcast_by_id(podcast_id, current_id)

    if podcast.needs_update:
        incomplete_obj.send_robust(sender=podcast)

    return podcast



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

    r = Podcast.view('podcasts/by_slug',
            startkey     = [slug, None],
            endkey       = [slug, {}],
            include_docs = True,
            wrap_doc     = False,
        )

    if not r:
        return None

    res = r.first()
    doc = res['doc']
    if doc['doc_type'] == 'Podcast':
        obj = Podcast.wrap(doc)
    else:
        pid = res['key'][1]
        pg = PodcastGroup.wrap(doc)
        obj = pg.get_podcast_by_id(pid)

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



@cache_result(timeout=60*60)
def podcast_for_oldid(oldid):

    if not oldid:
        raise QueryParameterMissing('oldid')

    r = Podcast.view('podcasts/by_oldid',
            key          = long(oldid),
            classes      = [Podcast, PodcastGroup],
            include_docs = True,
        )

    if not r:
        return None

    podcast_group = r.first()
    podcast = podcast_group.get_podcast_by_oldid(oldid)

    if podcast.needs_update:
        incomplete_obj.send_robust(sender=podcast)

    return podcast


@cache_result(timeout=60*60)
def podcastgroup_for_oldid(oldid):

    if not oldid:
        raise QueryParameterMissing('oldid')

    r = PodcastGroup.view('podcasts/groups_by_oldid',
            key          = long(oldid),
            include_docs = True,
        )

    if not r:
        return None

    pg = r.one()

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

    r = Podcast.view('podcasts/by_url',
            key=url,
            classes=[Podcast, PodcastGroup],
            include_docs=True
        )

    if r:
        podcast_group = r.first()
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

            obj = r['doc']
            if obj['doc_type'] == 'Podcast':
                yield Podcast.wrap(obj)

            elif obj['doc_type'] == 'PodcastGroup':
                yield PodcastGroup.wrap(obj)



def podcasts_by_last_update():
    res = Podcast.view('podcasts/by_last_update',
            include_docs = True,
            stale        = 'update_after',
            wrap_doc     = False,
        )

    # TODO: this method is only used for retrieving podcasts to update;
    #       should we really send 'incomplete_obj' signals here?

    return map(_wrap_podcast_group_key1, res)




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


def all_podcasts_groups(cls):
    return cls.view('podcasts/podcasts_groups', include_docs=True,
        classes=[Podcast, PodcastGroup]).iterator()



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



def podcasts_need_update():
    db = get_main_database()
    res = db.view('episodes/need_update',
            group_level = 1,
            reduce      = True,
            limit       = 100,
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
    r = list(Podcast.view('podcasts/flattr'))
    return r[0]['value']


def subscriberdata_for_podcast(podcast_id):

    if not podcast_id:
        raise QueryParameterMissing('podcast_id')

    r = PodcastSubscriberData.view('podcasts/subscriber_data',
            key          = podcast_id,
            include_docs = True,
        )

    if r:
        return r.first()

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

    #FIXME current couchdbkit can't parse responses for multi-query searches
    q = q.replace(',', '')

    try:
        res = db.search('podcasts/search',
                wrapper      = search_wrapper,
                include_docs = True,
                limit        = num_results,
                stale        = 'update_after',
                skip         = offset,
                q            = q,
                sort='\\subscribers<int>')

        podcasts = list(res)

        for podcast in podcasts:
            if podcast.needs_update:
                incomplete_obj.send_robust(sender=podcast)

        return podcasts, res.total_rows

    except RequestFailed:
        return [], 0


@repeat_on_conflict(['podcast'])
def update_additional_data(podcast, twitter):
    podcast.twitter = twitter
    podcast.save()

    # clear the whole cache until we have a better invalidation mechanism
    cache.clear()


@repeat_on_conflict(['podcast'])
def update_related_podcasts(podcast, related):
    if podcast.related_podcasts == related:
        return

    podcast.related_podcasts = related
    podcast.save()


@repeat_on_conflict(['podcast'])
def delete_podcast(podcast):
    podcast.delete()
