from collections import Counter

from mygpo.cel import celery
from mygpo.maintenance.merge import PodcastMerger
from mygpo.db.couchdb.podcast import podcasts_by_id

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


@celery.task
def merge_podcasts(podcast_ids, num_groups):
    """ Task to merge some podcasts"""

    logger.info('merging podcast ids %s', podcast_ids)

    podcasts = podcasts_by_id(podcast_ids)

    logger.info('merging podcasts %s', podcasts)

    actions = Counter()

    pm = PodcastMerger(podcasts, actions, num_groups)
    podcast = pm.merge()

    logger.info('merging result: %s', actions)

    return actions, podcast
