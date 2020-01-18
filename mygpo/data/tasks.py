from operator import itemgetter
from datetime import datetime, timedelta

from django.db import IntegrityError

from celery.decorators import periodic_task

from mygpo.data.podcast import calc_similar_podcasts
from mygpo.celery import celery
from mygpo.podcasts.models import Podcast

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@celery.task
def update_podcasts(podcast_urls):
    """ Task to update a podcast """
    from mygpo.data.feeddownloader import update_podcasts as update

    podcasts = update(podcast_urls)
    podcasts = filter(None, podcasts)
    return [podcast.pk for podcast in podcasts]


@celery.task
def update_related_podcasts(podcast_pk, max_related=20):
    get_podcast = itemgetter(0)

    podcast = Podcast.objects.get(pk=podcast_pk)

    related = calc_similar_podcasts(podcast)[:max_related]
    related = map(get_podcast, related)

    for p in related:
        try:
            podcast.related_podcasts.add(p)
        except IntegrityError:
            logger.warning(
                'Integrity error while adding related podcast', exc_info=True
            )


# interval in which podcast updates are scheduled
UPDATE_INTERVAL = timedelta(hours=1)


@periodic_task(run_every=UPDATE_INTERVAL)
def schedule_updates(interval=UPDATE_INTERVAL):
    """ Schedules podcast updates that are due within ``interval`` """
    now = datetime.utcnow()

    # max number of updates to schedule (one every 10s)
    max_updates = UPDATE_INTERVAL.total_seconds() / 10

    # fetch podcasts for which an update is due within the next hour
    podcasts = (
        Podcast.objects.all()
        .next_update_between(now, now + interval)
        .prefetch_related('urls')
        .only('pk')[:max_updates]
    )

    _schedule_updates(podcasts)


@periodic_task(run_every=UPDATE_INTERVAL)
def schedule_updates_longest_no_update():
    """ Schedule podcasts for update that have not been updated for longest """

    # max number of updates to schedule (one every 20s)
    max_updates = UPDATE_INTERVAL.total_seconds() / 10

    podcasts = Podcast.objects.order_by('last_update')[:max_updates]
    _schedule_updates(podcasts)


def _schedule_updates(podcasts):
    """ Schedule updates for podcasts """
    logger.info('Scheduling %d podcasts for update', len(podcasts))

    # queue all those podcast updates
    for podcast in podcasts:
        # update_podcasts.delay() seems to block other task execution,
        # therefore celery.send_task() is used instead
        urls = [podcast.url]
        celery.send_task('mygpo.data.tasks.update_podcasts', args=[urls])
