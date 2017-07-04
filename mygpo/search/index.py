
""" Contains code for indexing other objects """

from pyes import ES, QueryStringQuery, FunctionScoreQuery
from pyes.exceptions import IndexAlreadyExistsException, NoServerAvailable

from django.conf import settings

from mygpo.search.json import podcast_to_json
from mygpo.search.models import PodcastResult

import logging
logger = logging.getLogger(__name__)


def get_connection():
    """ Create a connection from Django settings """
    conn = ES([settings.ELASTICSEARCH_SERVER],
              timeout=settings.ELASTICSEARCH_TIMEOUT)
    return conn


def index_podcast(sender, **kwargs):
    """ Indexes a podcast """

    conn = get_connection()
    podcast = kwargs['instance']
    logger.info('Indexing podcast %s', podcast)

    document = podcast_to_json(podcast)

    try:
        conn.index(document, settings.ELASTICSEARCH_INDEX,
                   'podcast', podcast.id.hex)
    except NoServerAvailable:
        logger.exception('Indexing podcast failed')


def create_index():
    """ Creates the Elasticsearch index """
    conn = get_connection()

    logger.info('Creating index {0}', settings.ELASTICSEARCH_INDEX)
    try:
        conn.indices.create_index(settings.ELASTICSEARCH_INDEX)

    except IndexAlreadyExistsException as ex:
        logger.info(str(ex))


def search_podcasts(query):
    """ Search for podcasts according to 'query' """
    conn = get_connection()

    q = {
        "function_score" : {
            "boost_mode": 'replace',
            "query" : {
                 'simple_query_string': {'query': query}
            },
            "functions": [
                {
                    "script_score" : {
                       'script': "_score * doc.subscribers.value"
                    }
                }
            ]
        }
    }
    results = conn.search(query=q, indices=settings.ELASTICSEARCH_INDEX,
                          doc_types='podcast',
                          model=lambda conn, doc: PodcastResult.from_doc(doc))
    return results
