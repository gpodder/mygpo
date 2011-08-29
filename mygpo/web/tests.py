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

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

import mygpo.web.utils
from mygpo.test import create_auth_string


class SimpleWebTests(TestCase):
    def setUp(self):
        self.user, _ = User.objects.get_or_create(username='test')
        self.user.set_password('pwd')
        self.user.save()

        self.auth_string = create_auth_string('test', 'pwd')


    def test_access_parameterless_pages(self):
        pages = [
            'history',
            'suggestions',
            'tags',
            'help',
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
            'example-opml',
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
            self.client.post('/login/',
                dict(login_username=self.user.username, pwd='pwd'))

        for page in pages:
            response = self.client.get(reverse(page, args=args), follow=True)
            self.assertEquals(response.status_code, 200)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(mygpo.web.utils))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SimpleWebTests))
    return suite

