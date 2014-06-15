from mygpo.podcasts.models import Podcast
from mygpo.utils import is_url, normalize_feed_url
from mygpo.data.feeddownloader import PodcastUpdater, NoPodcastCreated
from mygpo.cache import cache_result
from mygpo.db.couchdb.podcast import search


@cache_result(timeout=60*60)
def search_podcasts(q, limit=20, skip=0):

    if is_url(q):
        url = normalize_feed_url(q)

        try:
            podcast = Podcast.objects.get(urls__url=url)
        except Podcast.DoesNotExist:
            podcast = None

        if not podcast or not podcast.title:

            updater = PodcastUpdater()

            try:
                updater.update(url)
            except NoPodcastCreated as npc:
                return [], 0

        try:
            podcast = Podcast.objects.get(urls__url=url)
            return [podcast], 1
        except Podcast.DoesNotExist:
            return [], 0


    return search(q, skip, limit)
