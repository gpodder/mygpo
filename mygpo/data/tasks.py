from operator import itemgetter

from mygpo.data.podcast import calc_similar_podcasts
from mygpo.celery import celery


@celery.task
def update_podcasts(podcast_urls):
    """ Task to update a podcast """
    from mygpo.data.feeddownloader import PodcastUpdater
    updater = PodcastUpdater()
    podcasts = updater.update_queue(podcast_urls)
    return list(podcasts)


@celery.task
def update_related_podcasts(podcast, max_related=20):
    get_podcast = itemgetter(0)

    related = calc_similar_podcasts(podcast)[:max_related]
    related = map(get_podcast, related)

    for p in related:
        podcast.related_podcasts.add(p)
