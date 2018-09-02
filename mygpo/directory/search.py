from mygpo.podcasts.models import Podcast
from mygpo.utils import is_url, normalize_feed_url
from mygpo.data.feeddownloader import PodcastUpdater, NoPodcastCreated
from mygpo.search.index import search_podcasts as search


def search_podcasts(q):

    if is_url(q):
        url = normalize_feed_url(q)

        try:
            podcast = Podcast.objects.get(urls__url=url)
        except Podcast.DoesNotExist:
            podcast = None

        updater = PodcastUpdater(url)

        if not podcast or not podcast.title:
            try:
                updater.update_podcast()
            except NoPodcastCreated as npc:
                return []

        try:
            podcast = Podcast.objects.get(urls__url=url)
            return [podcast]
        except Podcast.DoesNotExist:
            return []

    return search(q)
