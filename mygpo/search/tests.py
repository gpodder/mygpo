import uuid

from mygpo.podcasts.models import Podcast
from django.contrib.postgres.search import SearchVector
from django.test import TransactionTestCase
from django.test.utils import override_settings

from .index import search_podcasts
from .tasks import update_search_index


class SearchTests(TransactionTestCase):
    """ Tests podcast search """

    def test_search_podcast(self):
        """ Search if a podcast is found in the search results """

        # create a podcast
        podcast = Podcast(
            id=uuid.uuid1(),
            title="Awesome Podcast",
            description="An amazing podcast on many topics",
        )
        podcast.save()

        # explicitly trigger a search index update
        update_search_index()

        # search for the podcast
        results = search_podcasts("awesome")
        self.assertEqual(results[0].id, podcast.id)

    @override_settings(QUERY_LENGTH_CUTOFF=3)
    def test_shortest_search_podcast(self):
        """
        Search for a podcast with query length smaller than 3
        With QUERY_LENGTH_CUTOFF = 3
        Server would normally time out, however Podcasts exist for the given
        search term.
        """
        # create a podcast
        podcast = Podcast(
            id=uuid.uuid1(),
            title="The Tricky Podcast",
            description="The only podcast containing tricky messages.",
        )
        podcast.save()

        # explicitly trigger a search index update
        update_search_index()

        results = search_podcasts("The")
        self.assertEqual(len(results), 0)

        results = search_podcasts("The Tricky")
        self.assertEqual(results[0].id, podcast.id)
