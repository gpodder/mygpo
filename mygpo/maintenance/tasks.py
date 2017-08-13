import uuid

from mygpo.celery import celery
from mygpo.podcasts.models import Podcast

from . import models

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


@celery.task
def populate_merge_queue():
    """ Populate the merge queue with merge candidates """

    candidates = Podcast.objects.filter(mergequeueentry__isnull=True)

    for podcast in candidates.iterator():

        # randomly pick an episode
        episode = podcast.episode_set.order_by('?').first()

        if not episode:
            continue

        if not episode.url:
            continue

        # get a group of similar podcasts
        # it is sufficient to have one episode in common -- this could be
        # extended to require multiple common episodes
        podcasts = Podcast.objects.filter(episode__urls__url=episode.url)

        # a group of one is no real group -- there'd be nothing to merge
        if podcasts.count() <= 1:
            continue

        mqs = _get_merge_queues(podcasts)

        if len(mqs) == 0:
            mq = models.MergeTask.objects.create(id=uuid.uuid4())

        if len(mqs) == 1:
            mq = mqs.pop()

        if len(mqs) > 1:
            continue  # merge queues would need to be merged -- not yet supported

        for podcast in podcasts.iterator():

            # already in a merge queue
            if podcast.entries.exists():
                continue

            # add to merge queue
            mqe = models.MergeTaskEntry.objects.create(
                id=uuid.uuid4(),
                podcast=podcast,
                queue=mq,
            )


def _get_merge_queues(podcasts):
    mqs = models.MergeTask.objects.filter(
        mergequeueentry__podcast__in=podcasts,
    ).distinct()
    return set(mqs)
