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

from mygpo.api.opml import Importer, Exporter
from mygpo.api.models import Podcast, Device, UserProfile
from mygpo.test import create_auth_string

try:
    import simplejson as json
except ImportError:
    import json


class LegacyAPITests(TestCase):

    def setUp(self):
        self.user = User(username='test', email='test@gpodder.net')
        self.user.set_password('pwd')
        self.user.save()
        self.podcasts = [Podcast(url='http://test.com/asdf.xml'),
            Podcast(url='http://podcast.net/feed.xml')]

    def test_upload(self):
        exporter = Exporter('')
        response = self.client.post('/upload',
            dict(username=self.user.email, password='pwd',
                action='update-subscriptions', protocol=0,
                opml=exporter.generate(self.podcasts)))
        self.assertEqual(response.status_code, 200)

    def test_getlist(self):
        response = self.client.get('/getlist',
            dict(username=self.user.email, password='pwd'))
        self.assertEqual(response.status_code, 200)


class SimpleAPITests(TestCase):

    def setUp(self):
        self.user = User(username='test')
        self.user.set_password('pwd')
        self.user.save()
        self.device, _c = Device.objects.get_or_create(user=self.user, uid='dev')
        self.podcasts = [Podcast(url='http://test.com/asdf.xml'),
            Podcast(url='http://podcast.net/feed.xml')]
        self.auth_string = create_auth_string(self.user.username, 'pwd')

    def test_upload_subscriptions(self):
        response = self.client.post('/subscriptions/%s/%s.txt' %
                (self.user.username, self.device.uid),
                '\n'.join([p.url for p in self.podcasts]),
                content_type='text/plain',
                HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)

    def test_get_subscriptions(self):
        response = self.client.get('/subscriptions/%s/%s.json' %
            (self.user.username, self.device.uid),
            HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)

    def test_get_toplist(self):
        response = self.client.get('/toplist/30.opml')
        self.assertEqual(response.status_code, 200)

    def test_get_suggestions(self):
        response = self.client.get('/suggestions/30.opml',
            HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        response = self.client.get('/search.opml',
            dict(q='Tech'))
        self.assertEqual(response.status_code, 200)


class AdvancedAPITests(TestCase):

    def setUp(self):
        self.user = User(username='test')
        self.user.set_password('pwd')
        self.user.save()
        UserProfile.objects.get_or_create(user=self.user)
        self.device, _ = Device.objects.get_or_create(user=self.user, uid='dev')
        self.p1, _ = Podcast.objects.get_or_create(url='http://podcast.com/feed.xml')
        self.p2, _ = Podcast.objects.get_or_create(url='http://server.net/mp3.xml')
        self.auth_string = create_auth_string(self.user.username, 'pwd')

    def test_update_subscriptions(self):
        action = dict(add=[self.p1.url], remove=[self.p2.url])
        response = self.client.post('/api/1/subscriptions/%s/%s.json' %
            (self.user.username, self.device.uid),
            json.dumps(action),
            content_type='text/json',
            HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)

    def test_get_subscription_changes(self):
        response = self.client.get('/api/1/subscriptions/%s/%s.json' %
            (self.user.username, self.device.uid),
            dict(since=0),
            HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)

    def test_get_episode_actions(self):
        response = self.client.get('/api/2/episodes/%s.json' %
            self.user.username,
            dict(device=self.device.uid, since=10000),
            HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)

    def test_update_device(self):
         action = dict(caption='Test-Device', type='laptop')
         response = self.client.post('/api/2/devices/%s/%s.json' %
                (self.user.username, self.device.uid),
                json.dumps(action),
                content_type='text/json',
                HTTP_AUTHORIZATION=self.auth_string)
         self.assertEqual(response.status_code, 200)

    def test_device_list(self):
        response = self.client.get('/api/2/devices/%s.json' %
            self.user.username,
            HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)

    def test_get_top_tags(self):
        response = self.client.get('/api/2/tags/30.json')
        self.assertEqual(response.status_code, 200)

    def test_get_podcasts_for_tag(self):
        response = self.client.get('/api/2/tag/%s/30.json' %
            'Technology')
        self.assertEqual(response.status_code, 200)

    def test_get_podcast_data(self):
        response = self.client.get('/api/2/data/podcast.json',
            dict(url=self.p1.url))
        self.assertEqual(response.status_code, 200)

    def test_get_updates_for_device(self):
        response = self.client.get('/api/2/updates/%s/%s.json' %
            (self.user.username, self.device.uid),
            dict(since=0),
            HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)

    def test_save_setting(self):
        action = dict(set={'tested': True}, remove='setting')
        response = self.client.post('/api/2/settings/%s/account.json' %
            self.user.username,
            json.dumps(action),
            content_type='text/json',
            HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)

    def test_get_settings(self):
        response = self.client.get('/api/2/settings/%s/account.json' %
            self.user.username,
            HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)

    def test_get_favorite_episodes(self):
        response = self.client.get('/api/2/favorites/%s.json' %
            self.user.username,
            HTTP_AUTHORIZATION=self.auth_string)
        self.assertEqual(response.status_code, 200)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(LegacyAPITests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SimpleAPITests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(AdvancedAPITests))
    return suite
