

import uuid
import urllib.request, urllib.parse, urllib.error
import json

from django.core.urlresolvers import reverse
from django.test.client import Client as TestClient
from django.test import TestCase

from mygpo.test import create_auth_string, create_user
from mygpo.api.advanced import settings as views
from mygpo.usersettings.models import UserSettings
from mygpo.podcasts.models import Podcast, Episode
from mygpo.users.models import Client


class TestAPI(TestCase):

    def setUp(self):
        self.user, pwd = create_user()
        self.podcast_url = 'http://example.com/podcast.rss'
        self.episode_url = 'http://example.com/podcast/episode-1.mp3'
        self.uid = 'client-uid'
        self.podcast = Podcast.objects.get_or_create_for_url(self.podcast_url)
        self.episode = Episode.objects.get_or_create_for_url(
            self.podcast,
            self.episode_url,
        )
        self.user_client = Client.objects.create(
            id = uuid.uuid1(),
            user = self.user,
            uid = self.uid,
        )
        self.client = TestClient()
        self.extra = {
            'HTTP_AUTHORIZATION': create_auth_string(self.user.username, pwd)
        }

    def tearDown(self):
        self.user.delete()
        self.episode.delete()
        self.podcast.delete()

    def test_user_settings(self):
        """ Create, update and verify settings for the user """
        url = self.get_url(self.user.username, 'account')
        self._do_test_url(url)

    def test_podcast_settings(self):
        url = self.get_url(self.user.username, 'podcast', {
            'podcast': self.podcast_url,
        })
        self._do_test_url(url)

    def test_episode_settings(self):
        url = self.get_url(self.user.username, 'episode', {
            'podcast': self.podcast_url,
            'episode': self.episode_url,
        })
        self._do_test_url(url)

    def test_client_settings(self):
        url = self.get_url(self.user.username, 'device', {
            'device': self.uid,
        })
        self._do_test_url(url)

    def _do_test_url(self, url):
        # set settings
        settings = {'set': {'a': 'b', 'c': 'd'}}
        resp = self.client.post(url, json.dumps(settings),
                                content_type='application/octet-stream',
                                **self.extra)
        self.assertEqual(resp.status_code, 200, resp.content)

        # update settings
        settings = {'set': {'a': 'x'}, 'remove': ['c']}
        resp = self.client.post(url, json.dumps(settings),
                                content_type='application/octet-stream',
                                **self.extra)
        self.assertEqual(resp.status_code, 200, resp.content)

        # get settings
        resp = self.client.get(url, **self.extra)
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(json.loads(resp.content.decode('utf-8')), {'a': 'x'})

    def get_url(self, username, scope, params={}):
        url = reverse('settings-api', kwargs={
            'username': username,
            'scope': scope,
        })
        return '{url}?{params}'.format(url=url,
                                       params=urllib.parse.urlencode(params))
