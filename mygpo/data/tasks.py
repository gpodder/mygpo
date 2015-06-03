from operator import itemgetter
from datetime import datetime, timedelta

from celery.decorators import periodic_task

from mygpo.data.podcast import calc_similar_podcasts
from mygpo.celery import celery
from mygpo.podcasts.models import Podcast

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


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


# interval in which podcast updates are scheduled
UPDATE_INTERVAL = timedelta(hours=1)


@periodic_task(run_every=UPDATE_INTERVAL)
def schedule_updates(interval=UPDATE_INTERVAL):
    """ Schedules podcast updates that are due within ``interval`` """
    now = datetime.utcnow()

    # fetch podcasts for which an update is due within the next hour
    podcasts = Podcast.objects.all()\
                              .next_update_between(now, now+interval)\
                              .prefetch_related('urls')\
                              .only('pk')

    logger.error('Scheduling %d podcasts for update', podcasts.count())
    # queue all those podcast updates
    for podcast in podcasts:
        update_podcasts.delay([podcast.url])
