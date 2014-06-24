from restkit import RequestFailed

from mygpo.core.models import Podcast, PodcastGroup
from mygpo.core.signals import incomplete_obj
from mygpo.cache import cache_result
from mygpo.db.couchdb import get_main_database, lucene_query


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
