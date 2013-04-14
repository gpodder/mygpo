from collections import Counter

from mygpo.cel import celery
from mygpo.maintenance.merge import PodcastMerger
from mygpo.db.couchdb.podcast import podcasts_by_id


@celery.task
def merge_podcasts(podcast_ids, num_groups):
    """ Task to merge some podcasts"""

    podcasts = podcasts_by_id(podcast_ids)

    actions = Counter()

    pm = PodcastMerger(podcasts, actions, num_groups)
    pm.merge

    return actions, podcasts[0]
