import uuid
from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from mygpo.users.models import Client
from mygpo.podcasts.models import Podcast
from . import models


class TestSubscribe(TestCase):
    """Test subscribing to podcasts"""

    def setUp(self):
        User = get_user_model()
        self.user = User(
            username="duplicate-subscribe", email="duplicate-subscribe@example.com"
        )
        self.user.set_password("secret")
        self.user.save()
        self.client = Client.objects.create(user=self.user, uid="dev1", id=uuid.uuid1())

        self.url = "http://www.example.com/pdocast.rss"
        self.podcast = Podcast.objects.get_or_create_for_url(self.url).object

    def test_duplicate_subscribe(self):
        """Test that a duplicate subscription is skipped"""
        from mygpo.subscriptions.tasks import _perform_subscribe

        clients = [self.client, self.client]
        changed_clients = list(
            _perform_subscribe(
                self.podcast, self.user, clients, datetime.utcnow(), self.url
            )
        )

        # ensure only one client is changed
        self.assertEqual(len(changed_clients), 1)
        self.assertEqual(changed_clients[0], self.client)

        # ensure exactly one subscription has been created
        subscriptions = models.Subscription.objects.filter(
            podcast=self.podcast, user=self.user
        )
        self.assertEqual(subscriptions.count(), 1)
        subscriptions[0].delete()

    def tearDown(self):
        self.podcast.delete()
        self.client.delete()
        self.user.delete()
