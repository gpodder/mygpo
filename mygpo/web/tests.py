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

from django.test import TestCase
import unittest
import doctest

import mygpo.web.utils
from mygpo.test import create_auth_string
from django.contrib.auth.models import User

class SimpleWebTests(TestCase):
    def setUp(self):
        self.user, _ = User.objects.get_or_create(username='test')
        self.user.set_password('pwd')
        self.user.save()

        self.auth_string = create_auth_string('test', 'pwd')
        self.paramterless_pages = [
            '/history/',
            '/suggestions/',
            '/tags/',
            '/online-help/',
            '/subscriptions/',
            '/download/subscriptions.opml',
            '/subscriptions/all.opml',
            '/favorites/',
            '/account',
            '/account/privacy',
            '/account/delete',
            '/share/',
            '/toplist/',
            '/toplist/episodes',
            '/gpodder-examples.opml',
            '/devices/',
            '/login/',
            '/logout/',
            '/']

    def test_access_parameterless_pages(self):
        self.client.post('/login/',
            dict(login_username=self.user.username, pwd='pwd'))

        for page in self.paramterless_pages:
            response = self.client.get(page, follow=True)
#                HTTP_AUTHORIZATION=self.auth_string)
            self.assertEquals(response.status_code, 200)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(mygpo.web.utils))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SimpleWebTests))
    return suite

