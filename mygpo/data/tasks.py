from mygpo.cel import celery
from mygpo.data.feeddownloader import PodcastUpdater


@celery.task
def update_podcast(podcast):
    """ Task to update a podcast """
    updater = PodcastUpdater([podcast])
    updater.update()
    return True
