
""" Contains code for searching podcasts

Uses django.contrib.postgres.search for searching. See docs at
https://docs.djangoproject.com/en/1.11/ref/contrib/postgres/search/

"""

from django.conf import settings

from mygpo.podcasts.models import Podcast
from django.db.models import F
from mygpo.search.json import podcast_to_json
from django.contrib.postgres.search import SearchVector

import logging
logger = logging.getLogger(__name__)


def search_podcasts(query):
    """ Search for podcasts according to 'query' """

    logger.debug('Searching for "{query}" podcasts"', query=query)

    #vector = SearchVector('title', weight='A') + \
    #         SearchVector('description', weight='B')
    query = SearchQuery(query)

    results = Podcast.objects.annotate(
        rank=SearchRank(F('search_vector'), query)
    ).order_by('-rank')

    logger.debug('Found {count} podcasts for "{query}"', count=len(results),
                 query=query)

    return results
