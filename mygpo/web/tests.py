import unittest
import doctest
import uuid
import os.path
from unittest.mock import patch, MagicMock

import requests
import responses

from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.auth.models import User

from mygpo.podcasts.models import Podcast, Episode, Slug, Tag
from mygpo.web.logo import CoverArt, get_logo_url
from mygpo.test import create_auth_string, anon_request



from unittest.mock import Mock
from django.utils.translation import gettext as _
from mygpo.web.templatetags.episodes import episode_status_text


import logging

from .templatetags.devices import device_icon

logger = logging.getLogger(__name__)


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

class DeviceTest(unittest.TestCase):
    @patch('mygpo.web.templatetags.devices.staticfiles_storage')
    @patch('mygpo.web.templatetags.devices.mark_safe')
    def test_device(self, mock_mark_safe, mock_staticfiles_storage):
        mock_mark_safe.return_value = "mark_safe"

        coverage = [False] * 6

        mock_device = MagicMock()
        mock_device.user_agent = "gPodder"
        mock_device.type = "desktop"

        result = device_icon(mock_device, coverage, staticfiles_storage=mock_staticfiles_storage)
        expected_html = 'mark_safe'
        self.assertEqual(result, expected_html)

        mock_device.user_agent = "Amarok"
        mock_device.type = "desktop"
        result = device_icon(mock_device, coverage, staticfiles_storage=mock_staticfiles_storage)
        expected_html = 'mark_safe'
        self.assertEqual(result, expected_html)

        mock_device.user_agent = "Podax"
        mock_device.type = "desktop"
        result = device_icon(mock_device, coverage, staticfiles_storage=mock_staticfiles_storage)
        expected_html = 'mark_safe'
        self.assertEqual(result, expected_html)

        mock_device.user_agent = "other"
        mock_device.type = "unknown"
        result = device_icon(mock_device, coverage, staticfiles_storage=mock_staticfiles_storage)
        expected_html = ""
        self.assertEqual(result, expected_html)

        mock_device.user_agent = "none"
        mock_device.type = "none"
        result = device_icon(mock_device, coverage, staticfiles_storage=mock_staticfiles_storage)
        expected_html = ""
        self.assertEqual(result, expected_html)

        write_coverage_report("/home/hussein/sep/fork/mygpo/coverage/hussein/device_icon_coverage.txt", coverage,
                              "web/templatetags/devices.py", "device_icons")

class TestEpisodeStatusText(TestCase):
    def test_episode_status_text(self):
        coverage = [False] * 12

        # Create a mock device with a name attribute
        MockDevice = Mock()
        MockDevice.name = "Device1"

        # Create a mock Episode object with the mock device
        MockEpisode = Mock()
        MockEpisode.action = "new"  # Example action, change as needed
        MockEpisode.device = MockDevice


        # Test branch 0
        MockEpisode.action = None
        self.assertEqual(episode_status_text(MockEpisode, coverage), "")

        #Test branch 1
        MockEpisode.action = ""
        episode_status_text(MockEpisode, coverage), ""

        # Test branch 2
        # Test episode with action "new"
        MockEpisode.action = "new"
        self.assertEqual(episode_status_text(MockEpisode, coverage), "New episode")

        # Test branch 3 4
        # Test download action with specific device
        MockEpisode.action = "download"
        self.assertEqual(episode_status_text(MockEpisode, coverage), "Downloaded to Device1")

        # Test branch 3 5 
        # Test download action without specific device 
        MockEpisode.action = "download"
        MockDevice.name = None
        self.assertEqual(episode_status_text(MockEpisode, coverage), "Downloaded")

        # Test branch 6 7
        # Test play action with specific device
        MockEpisode.action = "play"
        MockDevice.name = "Device1"
        self.assertEqual(episode_status_text(MockEpisode, coverage), "Played on Device1")

        # Test branch 6 8
        # Test play action without specific device
        MockEpisode.action = "play"
        MockDevice.name = None
        self.assertEqual(episode_status_text(MockEpisode, coverage), "Played")

        # Test branch 9 10
        # Test delete action with specific device
        MockEpisode.action = "delete"
        MockDevice.name = "Device1"
        self.assertEqual(episode_status_text(MockEpisode, coverage), "Deleted on Device1")

        # Test branch 9 11
        # Test delete action without specific device
        MockEpisode.action = "delete"
        MockDevice.name = None
        self.assertEqual(episode_status_text(MockEpisode, coverage), "Deleted")

        write_coverage_to_file(
            "/Users/samuelpower/Desktop/SEP2/coverage.txt",
            "episode status",
            coverage,
        )


def write_coverage_to_file(filename, method_name, branch_coverage):
    total = len(branch_coverage)
    num_taken = 0
    with open(filename, 'w') as file:
        file.write(f"FILE: {filename}\nMethod: {method_name}\n")
        for index, coverage in enumerate(branch_coverage):
            if coverage:
                file.write(f"Branch {index} was taken\n")
                num_taken += 1
            else:
                file.write(f"Branch {index} was not taken\n")
        file.write("\n")
        coverage_level = num_taken/total * 100
        file.write(f"Total coverage = {coverage_level}%\n")

