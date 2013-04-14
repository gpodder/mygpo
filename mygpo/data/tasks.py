from mygpo.cel import celery
from mygpo.data.feeddownloader import PodcastUpdater


@celery.task
def update_podcasts(podcast_urls):
    """ Task to update a podcast """
    updater = PodcastUpdater()
    podcasts = updater.update_queue(podcast_urls)
    return list(podcasts)
