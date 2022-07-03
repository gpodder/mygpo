from collections import Counter
from celery.app import shared_task

from django_db_geventpool.utils import close_connection

from mygpo.podcasts.models import Podcast
from mygpo.maintenance.merge import PodcastMerger

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@shared_task
@close_connection
def merge_podcasts(podcast_ids, num_groups):
    """Task to merge some podcasts"""

    logger.info("merging podcast ids %s", podcast_ids)

    podcasts = list(Podcast.objects.filter(id__in=podcast_ids))

    logger.info("merging podcasts %s", podcasts)

    actions = Counter()

    pm = PodcastMerger(podcasts, actions, num_groups)
    podcast = pm.merge()

    logger.info("merging result: %s", actions)

    return actions, podcast
