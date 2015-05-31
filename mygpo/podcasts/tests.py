#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

import unittest
import uuid
from datetime import datetime, timedelta

from django.test import TestCase

from mygpo.podcasts.models import Podcast, Episode


def create_podcast(**kwargs):
    return Podcast.objects.create(id=uuid.uuid1(), **kwargs)


class PodcastTests(unittest.TestCase):
    """ Test podcasts and their properties """

    def test_next_update(self):
        """ Test calculation of Podcast.next_update """
        last_update = datetime(2014, 0o3, 31, 11, 00)
        update_interval = 123  # hours

        # create an "old" podcast with update-information
        create_podcast(last_update=last_update, update_interval=update_interval)

        # the podcast should be the next to be updated
        p = Podcast.objects.all().order_by_next_update().first()

        # assert that the next_update property is calculated correctly
        self.assertEqual(p.next_update,
                         last_update + timedelta(hours=update_interval))


    def test_get_or_create_for_url(self):
        """ Test that get_or_create_for_url returns existing Podcast """
        URL = 'http://example.com/get_or_create.rss'
        p1 = Podcast.objects.get_or_create_for_url(URL)
        p2 = Podcast.objects.get_or_create_for_url(URL)
        self.assertEqual(p1.pk, p2.pk)

    def test_episode_count(self):
        """ Test if Podcast.episode_count is updated correctly """
        PODCAST_URL = 'http://example.com/podcast.rss'
        EPISODE_URL = 'http://example.com/episode%d.mp3'
        NUM_EPISODES=3

        p = Podcast.objects.get_or_create_for_url(PODCAST_URL)
        for n in range(NUM_EPISODES):
            Episode.objects.get_or_create_for_url(p, EPISODE_URL % (n, ))

        p = Podcast.objects.get(pk=p.pk)
        self.assertEqual(p.episode_count, NUM_EPISODES)

        # the episodes already exist this time -- no episode is created
        for n in range(NUM_EPISODES):
            Episode.objects.get_or_create_for_url(p, EPISODE_URL % (n, ))

        p = Podcast.objects.get(pk=p.pk)
        self.assertEqual(p.episode_count, NUM_EPISODES)

        real_count = Episode.objects.filter(podcast=p).count()
        self.assertEqual(real_count, NUM_EPISODES)


class PodcastGroupTests(unittest.TestCase):
    """ Test grouping of podcasts """

    def test_group(self):
        self.podcast1 = create_podcast()
        self.podcast2 = create_podcast()

        group = self.podcast1.group_with(self.podcast2, 'My Group', 'p1', 'p2')

        self.assertIn(self.podcast1, group.podcast_set.all())
        self.assertIn(self.podcast2, group.podcast_set.all())
        self.assertEqual(len(group.podcast_set.all()), 2)
        self.assertEqual(group.title, 'My Group')
        self.assertEqual(self.podcast1.group_member_name, 'p1')
        self.assertEqual(self.podcast2.group_member_name, 'p2')

        # add to group
        self.podcast3 = create_podcast()

        group = self.podcast1.group_with(self.podcast3, 'My Group', 'p1', 'p3')

        self.assertIn(self.podcast3, group.podcast_set.all())
        self.assertEqual(self.podcast3.group_member_name, 'p3')

        # add group to podcast
        self.podcast4 = create_podcast()

        group = self.podcast4.group_with(self.podcast1, 'My Group', 'p4', 'p1')

        self.assertIn(self.podcast4, group.podcast_set.all())
        self.assertEqual(self.podcast4.group_member_name, 'p4')


class SlugTests(TestCase):
    """ Test various slug functionality """

    def test_update_slugs(self):

        # this is the current number of queries when writing the test; this has
        # not been optimized in any particular way, it should just be used to
        # alert when something changes
        podcast = create_podcast()

        with self.assertNumQueries(8):
            # set the canonical slug
            podcast.set_slug('podcast-1')
            self.assertEqual(podcast.slug, 'podcast-1')

        with self.assertNumQueries(9):
            # set a new list of slugs
            podcast.set_slugs(['podcast-2', 'podcast-1'])
            self.assertEqual(podcast.slug, 'podcast-2')

        with self.assertNumQueries(2):
            # remove the canonical slug
            podcast.remove_slug('podcast-2')
            self.assertEqual(podcast.slug, 'podcast-1')

        with self.assertNumQueries(3):
            # add a non-canonical slug
            podcast.add_slug('podcast-3')
            self.assertEqual(podcast.slug, 'podcast-1')


def load_tests(loader, tests, ignore):
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(PodcastTests))
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(PodcastGroupTests))
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(SlugTests))
    return tests
