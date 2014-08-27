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

import uuid
from datetime import datetime
import unittest
from collections import Counter

from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast, Episode
from mygpo.users.models import EpisodeAction
from mygpo.maintenance.merge import PodcastMerger
from mygpo.utils import get_timestamp
from mygpo.db.couchdb.episode_state import episode_state_for_user_episode, \
    add_episode_actions


def u():
    return uuid.uuid1()


class SimpleMergeTests(TestCase):

    def setUp(self):
        self.podcast1 = Podcast.objects.get_or_create_for_url(
            'http://example.com/simple-merge-test-feed.rss',
            defaults={'title': 'Podcast 1'},
        )
        self.podcast2 = Podcast.objects.get_or_create_for_url(
            'http://simple-merge-test.org/podcast/',
            defaults={'title': 'Podcast 2'},
        )

        self.episode1 = Episode.objects.get_or_create_for_url(
            self.podcast1, 'http://example.com/simple-merge-test-episode1.mp3',
            defaults={
                'title': 'Episode 1 A',
            })
        self.episode2 = Episode.objects.get_or_create_for_url(
            self.podcast2, 'http://example.com/simple-merge-test-episode1.mp3',
            defaults={
                'title': 'Episode 1 B',
            })

    def test_merge_podcasts(self):
        merge(self.podcast1, self.podcast2)


@override_settings(CACHE={})
class MergeTests(TransactionTestCase):
    """ Tests merging of two podcasts, their episodes and states """

    def setUp(self):
        self.podcast1 = Podcast.objects.get_or_create_for_url(
            'http://example.com/merge-test-feed.rss',
            defaults={'title': 'Podcast 1'},
        )
        self.podcast2 = Podcast.objects.get_or_create_for_url(
            'http://merge-test.org/podcast/',
            defaults={'title': 'Podcast 2'},
        )

        self.episode1 = Episode.objects.get_or_create_for_url(
            self.podcast1, 'http://example.com/merge-test-episode1.mp3',
            defaults={
                'title': 'Episode 1 A',
            })
        self.episode2 = Episode.objects.get_or_create_for_url(
            self.podcast2, 'http://example.com/merge-test-episode1.mp3',
            defaults={
                'title': 'Episode 1 B',
            })

        User = get_user_model()
        self.user = User(username='test-merge')
        self.user.email = 'test-merge-tests@example.com'
        self.user.set_password('secret!')
        self.user.save()

    def test_merge_podcasts(self):

        # Create additional data that will be merged
        state1 = episode_state_for_user_episode(self.user, self.episode1)
        state2 = episode_state_for_user_episode(self.user, self.episode2)

        action1 = EpisodeAction(action='play',
                                timestamp=datetime.utcnow(),
                                upload_timestamp=get_timestamp(
                                    datetime.utcnow()))
        action2 = EpisodeAction(action='download',
                                timestamp=datetime.utcnow(),
                                upload_timestamp=get_timestamp(
                                    datetime.utcnow()))

        add_episode_actions(state1, [action1])
        add_episode_actions(state2, [action2])

        # decide which episodes to merge
        groups = [(0, [self.episode1, self.episode2])]
        counter = Counter()

        pm = PodcastMerger([self.podcast1, self.podcast2], counter, groups)
        pm.merge()

        state1 = episode_state_for_user_episode(self.user, self.episode1)

        # both actions must be present in state1
        self.assertIn(action1, state1.actions)
        self.assertIn(action2, state1.actions)

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
        )
        self.podcast2 = Podcast.objects.get_or_create_for_url(
            'http://test.org/group-merge-podcast/',
            defaults={
                'title': 'Podcast 2',
            },
        )
        self.podcast3 = Podcast.objects.get_or_create_for_url(
            'http://group-test.org/feed/',
            defaults={
                'title': 'Podcast 3',
            },
        )

        self.episode1 = Episode.objects.get_or_create_for_url(
            self.podcast1, 'http://example.com/group-merge-episode1.mp3',
            defaults={
                'title': 'Episode 1 A',
            },
        )
        self.episode2 = Episode.objects.get_or_create_for_url(
            self.podcast2, 'http://example.com/group-merge-episode1.mp3',
            defaults={
                'title': 'Episode 1 B',
            },
        )
        self.episode3 = Episode.objects.get_or_create_for_url(
            self.podcast3, 'http://example.com/group-merge-media.mp3',
            defaults={
                'title': 'Episode 2',
            },
        )

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

        # Create additional data that will be merged
        state1 = episode_state_for_user_episode(self.user, self.episode1)
        state2 = episode_state_for_user_episode(self.user, self.episode2)

        action1 = EpisodeAction(action='play',
                                timestamp=datetime.utcnow(),
                                upload_timestamp=get_timestamp(
                                    datetime.utcnow()))
        action2 = EpisodeAction(action='download',
                                timestamp=datetime.utcnow(),
                                upload_timestamp=get_timestamp(
                                    datetime.utcnow()))

        add_episode_actions(state1, [action1])
        add_episode_actions(state2, [action2])

        # decide which episodes to merge
        groups = [(0, [self.episode1, self.episode2])]
        counter = Counter()

        episode2_id = self.episode2.id

        pm = PodcastMerger([podcast2, podcast1], counter, groups)
        pm.merge()

        state1 = episode_state_for_user_episode(self.user, self.episode1)

        self.assertIn(action1, state1.actions)
        self.assertIn(action2, state1.actions)

        episode1 = Episode.objects.get(pk=self.episode1.pk)

        # episode2 has been merged into episode1, so it must contain its
        # merged _id
        self.assertEqual([x.uuid for x in episode1.merged_uuids.all()],
                         [episode2_id])

    def tearDown(self):
        self.episode1.delete()
        self.podcast2.delete()
        self.user.delete()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MergeTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MergeGroupTests))
    return suite
