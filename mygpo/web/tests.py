import unittest
import doctest
import uuid
import os.path

import requests
import responses

from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast, Episode, Slug
import mygpo.web.utils
from mygpo.web.logo import CoverArt, get_logo_url
from mygpo.test import create_auth_string, anon_request

import logging

logger = logging.getLogger(__name__)


IMG_PATH1 = os.path.abspath(
    os.path.join(settings.BASE_DIR, '..', 'res', 'gpoddernet_228.png')
)

IMG_PATH2 = os.path.abspath(
    os.path.join(settings.BASE_DIR, '..', 'res', 'gpoddernet_16.png')
)


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
            'home',
        ]

        self.access_pages(pages, [], True)

    def test_access_podcast_pages(self):
        pages = ['podcast']

    def access_pages(self, pages, args, login):
        if login:
            self.client.post(
                '/login/', dict(login_username=self.user.username, pwd='pwd')
            )

        for page in pages:
            response = self.client.get(reverse(page, args=args), follow=True)
            self.assertEqual(response.status_code, 200)


class PodcastPageTests(TestCase):
    """ Test the podcast page """

    def setUp(self):
        # create a podcast and some episodes
        podcast = Podcast.objects.create(
            id=uuid.uuid1(), title='My Podcast', max_episode_order=1
        )
        for n in range(20):
            episode = Episode.objects.get_or_create_for_url(
                podcast, 'http://www.example.com/episode%d.mp3' % (n,)
            ).object

            # we only need (the last) one
            self.episode_slug = Slug.objects.create(
                content_object=episode, order=0, scope=podcast.as_scope, slug=str(n)
            )

        self.podcast_slug = Slug.objects.create(
            content_object=podcast, order=n, scope=podcast.scope, slug='podcast'
        )

    def test_podcast_queries(self):
        """ Test that the expected number of queries is executed """
        url = reverse('podcast-slug', args=(self.podcast_slug.slug,))
        # the number of queries must be independent of the number of episodes

        with self.assertNumQueries(5):
            anon_request(url)

    def test_episode_queries(self):
        """ Test that the expected number of queries is executed """
        url = reverse(
            'episode-slug', args=(self.podcast_slug.slug, self.episode_slug.slug)
        )

        with self.assertNumQueries(5):
            anon_request(url)


class PodcastLogoTests(TestCase):
    def setUp(self):
        # create a podcast
        self.URL = 'http://example.com/{}.png'.format(uuid.uuid1().hex)
        self.podcast = Podcast.objects.create(
            id=uuid.uuid1(), title='My Podcast', max_episode_order=1, logo_url=self.URL
        )
        self.client = Client()

    def tearDown(self):
        self.podcast.delete()

    def _save_logo(self):
        with responses.RequestsMock() as rsps, open(IMG_PATH1, 'rb') as body:
            rsps.add(
                responses.GET, self.URL, status=200, body=body, content_type='image/png'
            )

            CoverArt.save_podcast_logo(self.URL)

    def _fetch_cover(self, podcast, size=32):
        logo_url = get_logo_url(podcast, size)

        response = self.client.get(logo_url)
        self.assertEqual(302, response.status_code)
        redir = response['Location']

        logger.warning('Redirecting to {}'.format(redir))

        response = self.client.get(redir)
        self.assertEqual(200, response.status_code)
        return response

    def test_save_logo(self):
        self._save_logo()
        self._fetch_cover(self.podcast)

    def test_get_nonexisting(self):
        URL = 'http://example.com/non-existing-logo.png'

        self.podcast.logo_url = URL

        logo_url = get_logo_url(self.podcast, 32)

        response = self.client.get(logo_url)
        self.assertEqual(404, response.status_code)

    def test_get_existing_thumbnail(self):
        """ Retrieve an already existing thumbnail

        No distinction is visible outside, but it covers different
        code paths """

        self._save_logo()
        logo_url = get_logo_url(self.podcast, 32)

        response = self.client.get(logo_url)
        self.assertEqual(302, response.status_code, response.content)

        response = self.client.get(logo_url)
        self.assertEqual(302, response.status_code, response.content)

    def test_save_empty_logo(self):
        """ Make sure that save_podcast_logo(None) does not fail """
        try:
            CoverArt.save_podcast_logo(None)
        except:
            self.fail(
                'CoverArt.save_podcast_logo(None) should not raise ' 'an exception'
            )

    def test_exception_during_fetch(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                self.URL,
                body=requests.exceptions.RequestException('Fetching URL failed'),
            )

            CoverArt.save_podcast_logo(self.URL)

    def test_error_open_file(self):
        class ErrFileSystemStorage(FileSystemStorage):
            def open(*args, **kwargs):
                raise IOError

        self._save_logo()
        from mygpo.web import logo

        _logo_storage = logo.LOGO_STORAGE
        logo.LOGO_STORAGE = ErrFileSystemStorage(location=settings.MEDIA_ROOT)

        logo_url = get_logo_url(self.podcast, 32)

        response = self.client.get(logo_url)
        self.assertEqual(404, response.status_code)

        logo.LOGO_STORAGE = _logo_storage

    def test_new_logo(self):
        with responses.RequestsMock() as rsps, open(IMG_PATH1, 'rb') as body1, open(
            IMG_PATH1, 'rb'
        ) as body2, open(IMG_PATH2, 'rb') as body3:
            rsps.add(
                responses.GET,
                self.URL,
                status=200,
                body=body1,
                content_type='image/png',
            )
            rsps.add(
                responses.GET,
                self.URL,
                status=200,
                body=body2,
                content_type='image/png',
            )
            rsps.add(
                responses.GET,
                self.URL,
                status=200,
                body=body3,
                content_type='image/png',
            )

            logo_url = get_logo_url(self.podcast, 32)

            # first request
            CoverArt.save_podcast_logo(self.URL)
            response1 = self._fetch_cover(self.podcast)

            # stayed the same
            CoverArt.save_podcast_logo(self.URL)
            response2 = self._fetch_cover(self.podcast)

            self.assertEqual(
                list(response1.streaming_content), list(response2.streaming_content)
            )

            # changed
            CoverArt.save_podcast_logo(self.URL)
            response3 = self._fetch_cover(self.podcast)

            self.assertNotEqual(
                list(response2.streaming_content), list(response3.streaming_content)
            )
