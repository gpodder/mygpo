import uuid
import unittest

from mygpo.podcasts.models import Podcast
from django.contrib.postgres.search import SearchVector

from .index import search_podcasts
from .tasks import update_search_index


class SearchTests(unittest.TestCase):
    """ Tests podcast search """

    def test_search_podcast(self):
        """ Search if a podcast is found in the search results """

        # create a podcast
        podcast = Podcast(
            id=uuid.uuid1(),
            title='Awesome Podcast',
            description='An amazing podcast on many topics',
        )
        podcast.save()

        # explicitly trigger a search index update
        update_search_index()

        # search for the podcast
        results = search_podcasts('awesome')
        self.assertEqual(results[0].id, podcast.id)
