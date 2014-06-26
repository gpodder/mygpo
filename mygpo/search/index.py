
""" Contains code for indexing other objects """

from pyes import ES
from pyes.exceptions import IndexAlreadyExistsException

from django.conf import settings

import logging
logger = logging.getLogger(__name__)


def index_podcast(sender, **kwargs):
    print kwargs


def create_index():
    """ Creates the Elasticsearch index """
    conn = ES(settings.ELASTICSEARCH_SERVER)

    logger.info('Creating index %s' % settings.ELASTICSEARCH_INDEX)
    try:
        conn.indices.create_index(settings.ELASTICSEARCH_INDEX)

    except IndexAlreadyExistsException as ex:
        logger.info(str(ex))

