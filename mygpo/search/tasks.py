from datetime import timedelta

from celery.decorators import periodic_task

from django.db import transaction
from django.contrib.postgres.search import SearchVector

from mygpo.podcasts.models import Podcast

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)


# interval in which podcast updates are scheduled
UPDATE_INTERVAL = timedelta(hours=1)

# Maximum number of podcasts to update in one job run
MAX_INDEX = 1000


@periodic_task(run_every=UPDATE_INTERVAL)
def update_search_index(run_every=UPDATE_INTERVAL):
    """ Schedules podcast updates that are due within ``interval`` """

    logger.info('Updating search index')

    # We avoid an UPDATE, because it cannot be LIMITed, the thus might
    # be to expensive in a single statement.
    # We could use select_for_update(), but there is no need for consistency
    # between multiple podcasts.
    to_update = Podcast.objects\
        .filter(search_index_uptodate=False)\
        .only('pk')[:MAX_INDEX]

    count = to_update.count()
    logger.info('Updating search index for {} podcasts'.format(count))

    for podcast in to_update:
        Podcast.objects.filter(pk=podcast.pk)\
            .update(search_vector=
                        SearchVector('title', weight='A') +
                        SearchVector('description', weight='B'),
		            search_index_uptodate=True,
        )

    logger.info('Finished indexing podcasts')
