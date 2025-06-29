import functools
import operator
from datetime import timedelta

from celery import shared_task
from django_db_geventpool.utils import close_connection

from django.contrib.postgres.search import SearchVector

from mygpo.podcasts.models import Podcast

from . import INDEX_FIELDS

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


# interval in which podcast updates are scheduled
UPDATE_INTERVAL = timedelta(hours=1)

# Maximum number of podcasts to update in one job run
MAX_INDEX = 1000


@shared_task(run_every=UPDATE_INTERVAL)
@close_connection
def update_search_index(run_every=UPDATE_INTERVAL):
    """Schedules podcast updates that are due within ``interval``"""

    logger.info("Updating search index")

    # We avoid an UPDATE, because it cannot be LIMITed, the thus might
    # be to expensive in a single statement.
    # We could use select_for_update(), but there is no need for consistency
    # between multiple podcasts.
    to_update = Podcast.objects.filter(search_index_uptodate=False).only("pk")[
        :MAX_INDEX
    ]

    count = to_update.count()
    logger.info("Updating search index for {} podcasts".format(count))

    vectors = _get_search_vectors()

    for podcast in to_update:
        Podcast.objects.filter(pk=podcast.pk).update(
            search_vector=vectors, search_index_uptodate=True
        )

    logger.info("Finished indexing podcasts")


def _get_search_vectors():
    """Return the combined search vector to use for indexing podcasts"""
    vectors = []
    for field, weight in INDEX_FIELDS.items():
        # index the podcast based on the stored language
        vectors.append(SearchVector(field, weight=weight))

    # vectors can be combined with +
    return functools.reduce(operator.__add__, vectors)
