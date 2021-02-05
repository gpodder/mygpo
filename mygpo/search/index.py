""" Contains code for searching podcasts

Uses django.contrib.postgres.search for searching. See docs at
https://docs.djangoproject.com/en/1.11/ref/contrib/postgres/search/

"""

from django.conf import settings

from mygpo.podcasts.models import Podcast

from django.db.models import F, FloatField, ExpressionWrapper
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


SEARCH_CUTOFF = settings.SEARCH_CUTOFF


def search_podcasts(query):
    """ Search for podcasts according to 'query' """
    if is_query_too_short(query):
        logger.debug('Found no podcasts for "{query}". Query is too short', query=query)
        return Podcast.objects.none()

    logger.debug('Searching for "{query}" podcasts"', query=query)

    query = SearchQuery(query)

    results = (
        Podcast.objects.annotate(rank=SearchRank(F("search_vector"), query))
        .annotate(
            order=ExpressionWrapper(
                F("rank") * F("subscribers"), output_field=FloatField()
            )
        )
        .filter(rank__gte=SEARCH_CUTOFF)
        .order_by("-order")[:100]
    )

    logger.debug(
        'Found {count} podcasts for "{query}"', count=len(results), query=query
    )

    return results


def is_query_too_short(query):
    return len(query.replace(" ", "")) <= settings.QUERY_LENGTH_CUTOFF
