from mygpo.core.models import Podcast, PodcastGroup
from mygpo.utils import is_url
from mygpo.couchdb import get_main_database
from mygpo.data.feeddownloader import update_podcasts
from mygpo.api.sanitizing import sanitize_url


def search_wrapper(result):
    doc = result['doc']
    if doc['doc_type'] == 'Podcast':
        p = Podcast.wrap(doc)
    elif doc['doc_type'] == 'PodcastGroup':
        p = PodcastGroup.wrap(doc)
    p._id = result['id']
    return p


def search_podcasts(q, limit=20, skip=0):

    if is_url(q):
        url = sanitize_url(q)

        podcast = Podcast.for_url(url, create=True)

        if not podcast.title:
            update_podcasts([podcast])

        podcast = Podcast.for_url(url)

        return [podcast], 1


    db = get_main_database()

    #FIXME current couchdbkit can't parse responses for multi-query searches
    q = q.replace(',', '')

    res = db.search('podcasts/search', wrapper=search_wrapper,
        include_docs=True, limit=limit, skip=skip, q=q,
        sort='\\subscribers<int>')

    #FIXME: return empty results in case of search backend error
    try:
        return list(res), res.total_rows
    except:
        return [], 0
