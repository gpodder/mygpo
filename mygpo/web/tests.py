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
import doctest
import uuid

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast, Episode, Slug
import mygpo.web.utils
from mygpo.test import create_auth_string, anon_request


class SimpleWebTests(TestCase):

    @classmethod
    def setUpClass(self):
        User = get_user_model()
        self.user = User(username='web-test', email='web-test@example.com')
        self.user.set_password('pwd')
        self.user.save()

        self.auth_string = create_auth_string('test', 'pwd')

    @classmethod
    def tearDownClass(self):
        self.user.delete()

    def test_access_parameterless_pages(self):
        pages = [
            'history',
            'suggestions',
            'tags',
            'subscriptions',
            'subscriptions-opml',
            'favorites',
            'account',
            'privacy',
            'delete-account',
            'share',
            'toplist',
            'episode-toplist',
            'devices',
            'device-create',
            'login',
            'logout',
            'home']

        self.access_pages(pages, [], True)

    def test_access_podcast_pages(self):
        pages = ['podcast', ]

    def access_pages(self, pages, args, login):
        if login:
            self.client.post('/login/', dict(
                login_username=self.user.username, pwd='pwd'))

        for page in pages:
            response = self.client.get(reverse(page, args=args), follow=True)
            self.assertEquals(response.status_code, 200)


class PodcastPageTests(TestCase):
    """ Test the podcast page """

    def setUp(self):
        # create a podcast and some episodes
        podcast = Podcast.objects.create(id=uuid.uuid1(),
                                         title='My Podcast',
                                         max_episode_order=1,
                                         )
        for n in range(20):
            episode = Episode.objects.get_or_create_for_url(
                podcast,
                'http://www.example.com/episode%d.mp3' % (n, ),
            )

            # we only need (the last) one
            self.episode_slug = Slug.objects.create(content_object=episode,
                                                    order=0,
                                                    scope=podcast.as_scope,
                                                    slug=str(n),
                                                    )

        self.podcast_slug = Slug.objects.create(content_object=podcast,
                                                order=n, scope=podcast.scope,
                                                slug='podcast')

    def test_podcast_queries(self):
        """ Test that the expected number of queries is executed """
        url = reverse('podcast-slug', args=(self.podcast_slug.slug, ))
        # the number of queries must be independent of the number of episodes

        with self.assertNumQueries(5):
            anon_request(url)

    def test_episode_queries(self):
        """ Test that the expected number of queries is executed """
        url = reverse('episode-slug', args=(self.podcast_slug.slug,
                                            self.episode_slug.slug))

        with self.assertNumQueries(5):
            anon_request(url)


def load_tests(loader, tests, ignore):
    tests.addTest(doctest.DocTestSuite(mygpo.web.utils))
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(SimpleWebTests))
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(PodcastPageTests))
    return tests
