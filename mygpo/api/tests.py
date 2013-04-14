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
from copy import deepcopy

from django.test.client import Client
from django.core.urlresolvers import reverse

from mygpo.api.advanced import episodes
from mygpo.users.models import User
from mygpo.test import create_auth_string
from mygpo.core.json import json


class LegacyAPITests(unittest.TestCase):
    pass


class AdvancedAPITests(unittest.TestCase):

    def setUp(self):
        self.password = 'asdf'
        self.username = 'user2'
        self.user = User(username=self.username, email='user2@example.com')
        self.user.set_password(self.password)
        self.user.save()
        self.user.is_active = True
        self.client = Client()

        self.extra = {
            'HTTP_AUTHORIZATION': create_auth_string(self.username, self.password)
        }

        self.action_data = [
          {
           "podcast": "http://example.com/feed.rss",
           "episode": "http://example.com/files/s01e20.mp3",
           "device": "gpodder_abcdef123",
           "action": "download",
           "timestamp": "2009-12-12T09:00:00"
          },
          {
           "podcast": "http://example.org/podcast.php",
           "episode": "http://ftp.example.org/foo.ogg",
           "action": "play",
           "started": 15,
           "position": 120,
           "total":  500
          }
        ]



    def tearDown(self):
        self.user.delete()


    def test_episode_actions(self):
        url = reverse(episodes, kwargs=dict(version='2', username=self.user.username))

        # upload actions
        response = self.client.post(url, json.dumps(self.action_data),
                content_type="application/json", **self.extra)
        self.assertEqual(response.status_code, 200, response.content)


        # get all
        extra = deepcopy(self.extra)
        extra['since'] = 0

        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, 200, response.content)
        response_obj = json.loads(response.content)
        actions = response_obj['actions']
        self.assertTrue(self.compare_action_list(self.action_data, actions))


    def compare_action_list(self, as1, as2):
        for a1 in as1:
            found = False
            for a2 in as2:
                if self.compare_actions(a1, a2):
                    found = True

            if not found:
                raise ValueError('%s not found in %s' % (a1, as2))
                return False

        return True


    def compare_actions(self, a1, a2):
        for key, val in a1.items():
            if a2.get(key, None) != val:
                return False
        return True

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(AdvancedAPITests))
    return suite
