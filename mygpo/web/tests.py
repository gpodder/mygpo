import unittest
from unittest.mock import patch
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
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from django.utils.translation import gettext as _
from mygpo.web.templatetags.episodes import episode_status_icon, initialize_coverage, get_coverage_data, write_coverage_to_file


import logging

logger = logging.getLogger(__name__)

class Action:
    def __init__(self, action=None, timestamp=None, client=None, started=None, stopped=None):
        self.action = action
        self.timestamp = timestamp
        self.client = client
        self.started = started
        self.stopped = stopped

class MockUtils:
    @staticmethod
    def format_time(time):
        return time

class EpisodeStatusIconTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.coverage_data = initialize_coverage()

    @classmethod
    def tearDownClass(cls):
        project_root = "/mnt/c/Users/moham/Desktop/mygpo/mygpo/web"
        write_coverage_to_file(f"{project_root}/coverage.txt", "episode_status_icon", get_coverage_data())

    def test_no_action(self):
        action = Action()
        result = episode_status_icon(action)
        expected = '<img src="%s" alt="nothing" title="%s" />' % (
            static('nothing.png'), _("Unplayed episode"))
        self.assertEqual(result, mark_safe(expected))

    def test_flattr_action(self):
        action = Action(action='flattr')
        result = episode_status_icon(action)
        expected = '<img src="https://flattr.com/_img/icons/flattr_logo_16.png" alt="flattr" title="%s" />' % (_("The episode has been flattr'd"),)
        self.assertEqual(result, mark_safe(expected))

    def test_new_action(self):
        action = Action(action='new', timestamp='2022-01-01')
        result = episode_status_icon(action)
        expected = '<img src="%s" alt="new" title="%s" />' % (
            static('new.png'),
            "%s on 2022-01-01" % (_("This episode has been marked new")))
        self.assertEqual(result, mark_safe(expected))

    def test_download_action(self):
        action = Action(action='download', timestamp='2022-01-01')
        result = episode_status_icon(action)
        expected = '<img src="%s" alt="downloaded" title="%s" />' % (
            static('download.png'),
            "%s on 2022-01-01" % (_("This episode has been downloaded")))
        self.assertEqual(result, mark_safe(expected))

    @patch('mygpo.web.templatetags.episodes.utils.format_time', side_effect=MockUtils.format_time)
    def test_play_action_with_started_and_stopped(self, mock_format_time):
        action = Action(action='play', timestamp='2022-01-01', started='10:00', stopped='10:30')
        result = episode_status_icon(action)
        playback_info = _(" from %(start)s to %(end)s") % {
            "start": MockUtils.format_time(action.started),
            "end": MockUtils.format_time(action.stopped),
        }
        expected = '<img src="%s" alt="played" title="%s" />' % (
            static('playback.png'),
            "%s on 2022-01-01%s" % (_("This episode has been played"), playback_info))
        self.assertEqual(result, mark_safe(expected))

    @patch('mygpo.web.templatetags.episodes.utils.format_time', side_effect=MockUtils.format_time)
    def test_play_action_with_stopped_only(self, mock_format_time):
        action = Action(action='play', timestamp='2022-01-01', stopped='10:30')
        result = episode_status_icon(action)
        playback_info = _(" to position %s") % (
            MockUtils.format_time(action.stopped),
        )
        expected = '<img src="%s" alt="played" title="%s" />' % (
            static('playback.png'),
            "%s on 2022-01-01%s" % (_("This episode has been played"), playback_info))
        self.assertEqual(result, mark_safe(expected))

    @patch('mygpo.web.templatetags.episodes.utils.format_time', side_effect=MockUtils.format_time)
    def test_play_action_without_stopped(self, mock_format_time):
        action = Action(action='play', timestamp='2022-01-01')
        result = episode_status_icon(action)
        playback_info = ""
        expected = '<img src="%s" alt="played" title="%s" />' % (
            static('playback.png'),
            "%s on 2022-01-01%s" % (_("This episode has been played"), playback_info))
        self.assertEqual(result, mark_safe(expected))

    def test_delete_action(self):
        action = Action(action='delete', timestamp='2022-01-01')
        result = episode_status_icon(action)
        expected = '<img src="%s" alt="deleted" title="%s" />' % (
            static('delete.png'),
            "%s on 2022-01-01" % (_("This episode has been deleted")))
        self.assertEqual(result, mark_safe(expected))
        
    def test_unknown_action(self):
        action = Action(action='unknown')
        result = episode_status_icon(action)
        self.assertEqual(result, 'unknown')


IMG_PATH1 = os.path.abspath(
    os.path.join(settings.BASE_DIR, "..", "res", "gpoddernet_228.png")
)

IMG_PATH2 = os.path.abspath(
    os.path.join(settings.BASE_DIR, "..", "res", "gpoddernet_16.png")
)


class SimpleWebTests(TestCase):
    @classmethod
    def setUpClass(self):
        User = get_user_model()
        self.user = User(username="web-test", email="web-test@example.com")
        self.user.set_password("pwd")
        self.user.save()

        self.auth_string = create_auth_string("test", "pwd")

    @classmethod
    def tearDownClass(self):
        self.user.delete()

    def test_access_parameterless_pages(self):
        pages = [
            "history",
            "suggestions",
            "tags",
            "subscriptions",
            "subscriptions-opml",
            "favorites",
            "account",
            "privacy",
            "delete-account",
            "share",
            "toplist",
            "episode-toplist",
            "devices",
            "device-create",
            "login",
            "logout",
            "home",
        ]

        self.access_pages(pages, [], True)

    def test_access_podcast_pages(self):
        pages = ["podcast"]

    def access_pages(self, pages, args, login):
        if login:
            self.client.post(
                "/login/", dict(login_username=self.user.username, pwd="pwd")
            )

        for page in pages:
            response = self.client.get(reverse(page, args=args), follow=True)
            self.assertEqual(response.status_code, 200)


class PodcastPageTests(TestCase):
    """Test the podcast page"""

    def setUp(self):
        # create a podcast and some episodes
        podcast = Podcast.objects.create(
            id=uuid.uuid1(), title="My Podcast", max_episode_order=1
        )
        for n in range(20):
            episode = Episode.objects.get_or_create_for_url(
                podcast, "http://www.example.com/episode%d.mp3" % (n,)
            ).object

            # we only need (the last) one
            self.episode_slug = Slug.objects.create(
                content_object=episode, order=0, scope=podcast.as_scope, slug=str(n)
            )

        self.podcast_slug = Slug.objects.create(
            content_object=podcast, order=n, scope=podcast.scope, slug="podcast"
        )

    def test_podcast_queries(self):
        """Test that the expected number of queries is executed"""
        url = reverse("podcast-slug", args=(self.podcast_slug.slug,))
        # the number of queries must be independent of the number of episodes

        with self.assertNumQueries(5):
            anon_request(url)

    def test_episode_queries(self):
        """Test that the expected number of queries is executed"""
        url = reverse(
            "episode-slug", args=(self.podcast_slug.slug, self.episode_slug.slug)
        )

        with self.assertNumQueries(5):
            anon_request(url)


class PodcastLogoTests(TestCase):
    def setUp(self):
        # create a podcast
        self.URL = "http://example.com/{}.png".format(uuid.uuid1().hex)
        self.podcast = Podcast.objects.create(
            id=uuid.uuid1(), title="My Podcast", max_episode_order=1, logo_url=self.URL
        )
        self.client = Client()

    def tearDown(self):
        self.podcast.delete()

    def _save_logo(self):
        with responses.RequestsMock() as rsps, open(IMG_PATH1, "rb") as body:
            rsps.add(
                responses.GET, self.URL, status=200, body=body, content_type="image/png"
            )

            CoverArt.save_podcast_logo(self.URL)

    def _fetch_cover(self, podcast, size=32):
        logo_url = get_logo_url(podcast, size)

        response = self.client.get(logo_url)
        self.assertEqual(302, response.status_code)
        redir = response["Location"]

        logger.warning("Redirecting to {}".format(redir))

        response = self.client.get(redir)
        self.assertEqual(200, response.status_code)
        return response

    def test_save_logo(self):
        self._save_logo()
        self._fetch_cover(self.podcast)

    def test_get_nonexisting(self):
        URL = "http://example.com/non-existing-logo.png"

        self.podcast.logo_url = URL

        logo_url = get_logo_url(self.podcast, 32)

        response = self.client.get(logo_url)
        self.assertEqual(404, response.status_code)

    def test_get_existing_thumbnail(self):
        """Retrieve an already existing thumbnail

        No distinction is visible outside, but it covers different
        code paths"""

        self._save_logo()
        logo_url = get_logo_url(self.podcast, 32)

        response = self.client.get(logo_url)
        self.assertEqual(302, response.status_code, response.content)

        response = self.client.get(logo_url)
        self.assertEqual(302, response.status_code, response.content)

    def test_save_empty_logo(self):
        """Make sure that save_podcast_logo(None) does not fail"""
        try:
            CoverArt.save_podcast_logo(None)
        except:
            self.fail(
                "CoverArt.save_podcast_logo(None) should not raise " "an exception"
            )

    def test_exception_during_fetch(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                self.URL,
                body=requests.exceptions.RequestException("Fetching URL failed"),
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
        with responses.RequestsMock() as rsps, open(IMG_PATH1, "rb") as body1, open(
            IMG_PATH1, "rb"
        ) as body2, open(IMG_PATH2, "rb") as body3:
            rsps.add(
                responses.GET,
                self.URL,
                status=200,
                body=body1,
                content_type="image/png",
            )
            rsps.add(
                responses.GET,
                self.URL,
                status=200,
                body=body2,
                content_type="image/png",
            )
            rsps.add(
                responses.GET,
                self.URL,
                status=200,
                body=body3,
                content_type="image/png",
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


class PublisherPageTests(TestCase):
    """Test the publisher page"""

    @classmethod
    def setUpTestData(self):
        User = get_user_model()
        self.user = User(username="web-test", email="web-test@example.com")
        self.user.set_password("pwd")
        self.user.is_staff = True
        self.user.save()

    def test_publisher_detail_slug(self):
        # create a podcast with slug
        podcast = Podcast.objects.get_or_create_for_url(
            "http://example.com/podcast.rss"
        ).object
        slug = "test"
        podcast.set_slug(slug)

        url = reverse("podcast-publisher-detail-slug", args=(slug,))

        self.client.login(username="web-test", password="pwd")

        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_publisher_detail_id(self):
        # create a podcast with no slug
        podcast = Podcast.objects.get_or_create_for_url(
            "http://example.com/podcast2.rss"
        ).object

        url = reverse("podcast-publisher-detail-id", args=(podcast.id,))

        self.client.login(username="web-test", password="pwd")

        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
