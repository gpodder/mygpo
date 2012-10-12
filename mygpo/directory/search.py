from mygpo.utils import is_url
from mygpo.data.feeddownloader import PodcastUpdater
from mygpo.api.sanitizing import sanitize_url
from mygpo.cache import cache_result
from mygpo.db.couchdb.podcast import podcast_for_url, search


@cache_result(timeout=60*60)
def search_podcasts(q, limit=20, skip=0):

    if is_url(q):
        url = sanitize_url(q)

        podcast = podcast_for_url(url, create=True)

        if not podcast.title:
            updater = PodcastUpdater([podcast])
            updater.update()

        podcast = podcast_for_url(url)

        return [podcast], 1


    return search(q, skip, limit)
