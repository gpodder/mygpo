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
from django.core.urlresolvers import reverse, resolve
from django.test.client import RequestFactory
from django.contrib.auth.models import AnonymousUser

from mygpo.podcasts.models import Podcast, Episode, Slug
import mygpo.web.utils
from mygpo.users.models import User
from mygpo.test import create_auth_string


class SimpleWebTests(TestCase):

    @classmethod
    def setUpClass(self):
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
            'subscriptions-download',
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
        self.factory = RequestFactory()

        # create a podcast and some episodes
        podcast = Podcast.objects.create(id=uuid.uuid1().hex)
        for n in range(20):
            episode = Episode.objects.create(id=uuid.uuid1().hex,
                                             podcast=podcast,
                                            )
            slug = Slug.objects.create(content_object=episode, order=0,
                                       scope=podcast.scope, slug=str(n))

        self.slug = Slug.objects.create(content_object=podcast, order=n,
                                        scope=podcast.scope, slug='podcast')

    def test_queries(self):
        """ Test that the expected number of queries is executed """
        url = reverse('podcast-slug', args=(self.slug.slug, ))
        request = self.factory.get(url)
        request.user = AnonymousUser()
        view = resolve(url)

        # the number of queries must be independent of the number of episodes
        with self.assertNumQueries(5):
            response = view.func(request, *view.args, **view.kwargs)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(mygpo.web.utils))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SimpleWebTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(PodcastPageTests))
    return suite
