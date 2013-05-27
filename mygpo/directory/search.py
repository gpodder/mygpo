from mygpo.utils import is_url, normalize_feed_url
from mygpo.data.feeddownloader import PodcastUpdater, NoPodcastCreated
from mygpo.cache import cache_result
from mygpo.db.couchdb.podcast import podcast_for_url, search


@cache_result(timeout=60*60)
def search_podcasts(q, limit=20, skip=0):

    if is_url(q):
        url = normalize_feed_url(q)

        podcast = podcast_for_url(url, create=False)

        if not podcast or not podcast.title:

            updater = PodcastUpdater()

            try:
                updater.update(url)
            except NoPodcastCreated as npc:
                return [], 0

        podcast = podcast_for_url(url)
        if podcast:
            return [podcast], 1
        else:
            return [], 0


    return search(q, skip, limit)
