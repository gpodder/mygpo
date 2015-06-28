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


import json
import unittest
import doctest
from urllib.parse import urlencode
from copy import deepcopy

from django.test.client import Client
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast, Episode
from mygpo.api.advanced import episodes
from mygpo.test import create_auth_string, anon_request


class AdvancedAPITests(unittest.TestCase):

    def setUp(self):
        User = get_user_model()
        self.password = 'asdf'
        self.username = 'adv-api-user'
        self.user = User(username=self.username, email='user@example.com')
        self.user.set_password(self.password)
        self.user.save()
        self.user.is_active = True
        self.client = Client()

        self.extra = {
            'HTTP_AUTHORIZATION': create_auth_string(self.username,
                                                     self.password)
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
        url = reverse(episodes, kwargs={
            'version': '2',
            'username': self.user.username,
        })

        # upload actions
        response = self.client.post(url, json.dumps(self.action_data),
                                    content_type="application/json",
                                    **self.extra)
        self.assertEqual(response.status_code, 200, response.content)

        response = self.client.get(url, {'since': '0'}, **self.extra)
        self.assertEqual(response.status_code, 200, response.content)
        response_obj = json.loads(response.content.decode('utf-8'))
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


class SubscriptionAPITests(unittest.TestCase):
    """ Tests the Subscription API """

    def setUp(self):
        User = get_user_model()
        self.password = 'asdf'
        self.username = 'subscription-api-user'
        self.device_uid = 'test-device'
        self.user = User(username=self.username, email='user@example.com')
        self.user.set_password(self.password)
        self.user.save()
        self.user.is_active = True
        self.client = Client()

        self.extra = {
            'HTTP_AUTHORIZATION': create_auth_string(self.username,
                                                     self.password)
        }

        self.action_data = {
            'add': ['http://example.com/podcast.rss'],
        }

        self.url = reverse('subscriptions-api', kwargs={
            'version': '2',
            'username': self.user.username,
            'device_uid': self.device_uid,
        })

    def tearDown(self):
        self.user.delete()

    def test_set_get_subscriptions(self):
        """ Tests that an upload subscription is returned back correctly """

        # upload a subscription
        response = self.client.post(self.url, json.dumps(self.action_data),
                                    content_type="application/json",
                                    **self.extra)
        self.assertEqual(response.status_code, 200, response.content)

        # verify that the subscription is returned correctly
        response = self.client.get(self.url, {'since': '0'}, **self.extra)
        self.assertEqual(response.status_code, 200, response.content)
        response_obj = json.loads(response.content.decode('utf-8'))
        self.assertEqual(self.action_data['add'], response_obj['add'])
        self.assertEqual([], response_obj.get('remove', []))

    def test_unauth_request(self):
        """ Tests that an unauthenticated request gives a 401 response """
        response = self.client.get(self.url, {'since': '0'})
        self.assertEqual(response.status_code, 401, response.content)


class DirectoryTest(TestCase):
    """ Test Directory API """

    def setUp(self):
        self.podcast = Podcast.objects.get_or_create_for_url(
            'http://example.com/directory-podcast.xml',
            defaults = {
                'title': 'My Podcast',
            },
        )
        self.episode = Episode.objects.get_or_create_for_url(
            self.podcast,
            'http://example.com/directory-podcast/1.mp3',
            defaults = {
                'title': 'My Episode',
            },
        )
        self.client = Client()

    def test_episode_info(self):
        """ Test that the expected number of queries is executed """
        url = reverse('api-episode-info') + '?' + urlencode(
            (('podcast', self.podcast.url), ('url', self.episode.url)))

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)


def load_tests(loader, tests, ignore):
    tests.addTest(loader.loadTestsFromTestCase(AdvancedAPITests))
    tests.addTest(loader.loadTestsFromTestCase(SubscriptionAPITests))
    tests.addTest(loader.loadTestsFromTestCase(DirectoryTest))
    return tests
