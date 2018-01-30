import uuid
from datetime import datetime
import unittest
from collections import Counter

from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast, Episode
from mygpo.history.models import EpisodeHistoryEntry
from mygpo.maintenance.merge import PodcastMerger


def u():
    return uuid.uuid1()


class SimpleMergeTests(TestCase):

    def setUp(self):
        self.podcast1 = Podcast.objects.get_or_create_for_url(
            'http://example.com/simple-merge-test-feed.rss',
            defaults={'title': 'Podcast 1'},
        ).object
        self.podcast2 = Podcast.objects.get_or_create_for_url(
            'http://simple-merge-test.org/podcast/',
            defaults={'title': 'Podcast 2'},
        ).object

        self.episode1 = Episode.objects.get_or_create_for_url(
            self.podcast1, 'http://example.com/simple-merge-test-episode1.mp3',
            defaults={
                'title': 'Episode 1 A',
            }).object
        self.episode2 = Episode.objects.get_or_create_for_url(
            self.podcast2, 'http://example.com/simple-merge-test-episode1.mp3',
            defaults={
                'title': 'Episode 1 B',
            }).object

    def test_merge_podcasts(self):
        # decide which episodes to merge
        groups = [(0, [self.episode1, self.episode2])]
        counter = Counter()
        pm = PodcastMerger([self.podcast1, self.podcast2], counter, groups)
        pm.merge()


@override_settings(CACHE={})
class MergeTests(TransactionTestCase):
    """ Tests merging of two podcasts, their episodes and states """

    def setUp(self):
        self.podcast1 = Podcast.objects.get_or_create_for_url(
            'http://example.com/merge-test-feed.rss',
            defaults={'title': 'Podcast 1'},
        ).object
        self.podcast2 = Podcast.objects.get_or_create_for_url(
            'http://merge-test.org/podcast/',
            defaults={'title': 'Podcast 2'},
        ).object

        self.episode1 = Episode.objects.get_or_create_for_url(
            self.podcast1, 'http://example.com/merge-test-episode1.mp3',
            defaults={
                'title': 'Episode 1 A',
            }).object
        self.episode2 = Episode.objects.get_or_create_for_url(
            self.podcast2, 'http://example.com/merge-test-episode1.mp3',
            defaults={
                'title': 'Episode 1 B',
            }).object

        User = get_user_model()
        self.user = User(username='test-merge')
        self.user.email = 'test-merge-tests@example.com'
        self.user.set_password('secret!')
        self.user.save()

    def test_merge_podcasts(self):

        action1 = EpisodeHistoryEntry.create_entry(
            self.user,
            self.episode1,
            EpisodeHistoryEntry.PLAY,
        )

        action2 = EpisodeHistoryEntry.create_entry(
            self.user,
            self.episode2,
            EpisodeHistoryEntry.DOWNLOAD,
        )

        # decide which episodes to merge
        groups = [(0, [self.episode1, self.episode2])]
        counter = Counter()

        pm = PodcastMerger([self.podcast1, self.podcast2], counter, groups)
        pm.merge()

        history = EpisodeHistoryEntry.objects.filter(
            episode=self.episode1,
            user=self.user,
        )

        # both actions must be present for the merged episode
        self.assertIn(action1, history)
        self.assertIn(action2, history)

    def tearDown(self):
        self.episode1.delete()
        self.podcast1.delete()
        self.user.delete()


class MergeGroupTests(TransactionTestCase):
    """ Tests merging of two podcasts, one of which is part of a group """

    def setUp(self):
        self.podcast1 = Podcast.objects.get_or_create_for_url(
            'http://example.com/group-merge-feed.rss',
            defaults={
                'title': 'Podcast 1',
            },
        ).object
        self.podcast2 = Podcast.objects.get_or_create_for_url(
            'http://test.org/group-merge-podcast/',
            defaults={
                'title': 'Podcast 2',
            },
        ).object
        self.podcast3 = Podcast.objects.get_or_create_for_url(
            'http://group-test.org/feed/',
            defaults={
                'title': 'Podcast 3',
            },
        ).object

        self.episode1 = Episode.objects.get_or_create_for_url(
            self.podcast1, 'http://example.com/group-merge-episode1.mp3',
            defaults={
                'title': 'Episode 1 A',
            },
        ).object
        self.episode2 = Episode.objects.get_or_create_for_url(
            self.podcast2, 'http://example.com/group-merge-episode1.mp3',
            defaults={
                'title': 'Episode 1 B',
            },
        ).object
        self.episode3 = Episode.objects.get_or_create_for_url(
            self.podcast3, 'http://example.com/group-merge-media.mp3',
            defaults={
                'title': 'Episode 2',
            },
        ).object

        self.podcast2.group_with(self.podcast3, 'My Group', 'Feed1', 'Feed2')

        User = get_user_model()
        self.user = User(username='test-merge-group')
        self.user.email = 'test-merge-group-tests@example.com'
        self.user.set_password('secret!')
        self.user.save()

    def test_merge_podcasts(self):
        podcast1 = Podcast.objects.get(pk=self.podcast1.pk)
        podcast2 = Podcast.objects.get(pk=self.podcast2.pk)
        podcast3 = Podcast.objects.get(pk=self.podcast3.pk)

        # assert that the podcasts are actually grouped
        self.assertEqual(podcast2.group, podcast3.group)

        action1 = EpisodeHistoryEntry.create_entry(
            self.user,
            self.episode1,
            EpisodeHistoryEntry.PLAY,
        )

        action2 = EpisodeHistoryEntry.create_entry(
            self.user,
            self.episode2,
            EpisodeHistoryEntry.DOWNLOAD,
        )

        # decide which episodes to merge
        groups = [(0, [self.episode1, self.episode2])]
        counter = Counter()

        episode2_id = self.episode2.id

        pm = PodcastMerger([podcast2, podcast1], counter, groups)
        pm.merge()

        history = EpisodeHistoryEntry.objects.filter(
            episode = self.episode1,
            user = self.user,
        )

        self.assertIn(action1, history)
        self.assertIn(action2, history)

        episode1 = Episode.objects.get(pk=self.episode1.pk)

        # episode2 has been merged into episode1, so it must contain its
        # merged _id
        self.assertEqual([x.uuid for x in episode1.merged_uuids.all()],
                         [episode2_id])

    def tearDown(self):
        self.episode1.delete()
        self.podcast2.delete()
        self.user.delete()
