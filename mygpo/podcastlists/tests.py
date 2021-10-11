from django.urls import reverse
from django.test.client import Client
from django.test import TestCase

from mygpo.test import create_auth_string, create_user
from mygpo.api.advanced import lists as views
from mygpo.podcastlists.models import PodcastList


class TestAPI(TestCase):
    """Tests the Podcast List API"""

    def setUp(self):
        self.user, pwd = create_user()
        self.client = Client()
        self.extra = {"HTTP_AUTHORIZATION": create_auth_string(self.user.username, pwd)}

    def tearDown(self):
        self.user.delete()

    def test_create_missing_title(self):
        """verify error response when creating podcast list w/o title"""
        url = reverse(
            views.create, kwargs={"username": self.user.username, "format": "txt"}
        )

        urls = ["http://example.com/podcast.rss", "http://example.com/asdf.xml"]

        resp = self.client.post(
            url, "\n".join(urls), content_type="text/plain", **self.extra
        )
        self.assertEqual(resp.status_code, 400, resp.content)

    def test_create(self):
        """Create a podcast list and verify"""
        title = "My Podcast List"
        url = get_create_url(self.user.username, "txt", title)

        urls = ["http://example.com/podcast.rss", "http://example.com/asdf.xml"]

        resp = self.client.post(
            url, "\n".join(urls), content_type="text/plain", **self.extra
        )
        self.assertEqual(resp.status_code, 201, resp.content)

        # assert that the list has actually been created
        lists = PodcastList.objects.filter(user=self.user)
        self.assertEqual(1, len(lists))
        pl = lists[0]
        self.assertEqual(title, pl.title)
        self.assertEqual(len(urls), pl.entries.count())
        pl.delete()

    def test_replace(self):
        """Create, replace and delete a podcast list"""
        title = "My Podcast List"
        url = get_create_url(self.user.username, "txt", title)

        urls1 = [
            "http://example.com/podcast.rss",
            "http://example.com/asdf.xml",
            "http://example.com/test.rss",
        ]

        resp = self.client.post(
            url, "\n".join(urls1), content_type="text/plain", **self.extra
        )
        self.assertEqual(resp.status_code, 201, resp.content)

        # assert that the list has actually been created
        lists = PodcastList.objects.filter(user=self.user)
        self.assertEqual(1, len(lists))
        self.assertEqual(title, lists[0].title)

        # replace existing list; the lists's URL is returned
        # in the Location header
        url = resp["Location"]
        urls2 = [
            "http://example.com/test.rss",  # reordered
            "http://example.com/asdf.xml",
            "http://example.com/new.rss",
        ]  # new

        resp = self.client.put(
            url, "\n".join(urls2), content_type="text/plain", **self.extra
        )
        self.assertEqual(resp.status_code, 204, resp.content)

        # assert that the list has actually been updated
        resp = self.client.get(url, content_type="text/plain", **self.extra)
        resp_urls = [u for u in resp.content.decode("utf-8").split("\n") if u]
        self.assertEqual(urls2, resp_urls)

        # delete the list
        self.client.delete(url)


def get_create_url(username, fmt, title):
    return "{url}?title={title}".format(
        url=reverse(views.create, kwargs={"username": username, "format": fmt}),
        title=title,
    )
