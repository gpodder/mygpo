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

from datetime import datetime
import unittest
from collections import Counter

from django.test import TestCase
from django.test.utils import override_settings

from mygpo.core.models import Podcast, Episode
from mygpo.users.models import EpisodeAction, User
from mygpo.maintenance.merge import PodcastMerger
from mygpo.utils import get_timestamp
from mygpo.db.couchdb.podcast import podcast_by_id
from mygpo.db.couchdb.episode import episode_by_id
from mygpo.db.couchdb.episode_state import episode_state_for_user_episode, \
    add_episode_actions


@override_settings(CACHE={})
class MergeTests(TestCase):
    """ Tests merging of two podcasts, their episodes and states """

    def setUp(self):
        self.podcast1 = Podcast(urls=['http://example.com/feed.rss'])
        self.podcast2 = Podcast(urls=['http://test.org/podcast/'])
        self.podcast1.save()
        self.podcast2.save()

        self.episode1 = Episode(podcast=self.podcast1.get_id(),
                urls = ['http://example.com/episode1.mp3'])
        self.episode2 = Episode(podcast=self.podcast2.get_id(),
                urls = ['http://example.com/episode1.mp3'])

        self.episode1.save()
        self.episode2.save()

        self.user = User(username='test-merge')
        self.user.email = 'test@example.com'
        self.user.set_password('secret!')
        self.user.save()


    def test_merge_podcasts(self):

        # Create additional data that will be merged
        state1 = episode_state_for_user_episode(self.user, self.episode1)
        state2 = episode_state_for_user_episode(self.user, self.episode2)

        action1 = EpisodeAction(action='play',
                timestamp=datetime.utcnow(),
                upload_timestamp=get_timestamp(datetime.utcnow()))
        action2 = EpisodeAction(action='download',
                timestamp=datetime.utcnow(),
                upload_timestamp=get_timestamp(datetime.utcnow()))

        add_episode_actions(state1, [action1])
        add_episode_actions(state2, [action2])

        # copy of the object
        episode2 = episode_by_id(self.episode2._id)

        # decide which episodes to merge
        groups = [(0, [self.episode1, self.episode2])]
        counter = Counter()

        pm = PodcastMerger([self.podcast1, self.podcast2], counter, groups)
        pm.merge()

        state1 = episode_state_for_user_episode(self.user, self.episode1)
        state2 = episode_state_for_user_episode(self.user, episode2)

        self.assertIn(action1, state1.actions)
        self.assertIn(action2, state1.actions)
        self.assertEqual(state2._id, None)



    def tearDown(self):
        self.podcast1.delete()
        self.episode1.delete()

        #self.podcast2.delete()
        #self.episode2.delete()

        self.user.delete()



class MergeGroupTests(TestCase):
    """ Tests merging of two podcasts, one of which is part of a group """

    def setUp(self):
        self.podcast1 = Podcast(urls=['http://example.com/feed.rss'])
        self.podcast2 = Podcast(urls=['http://test.org/podcast/'])
        self.podcast3 = Podcast(urls=['http://test.org/feed/'])
        self.podcast1.save()
        self.podcast2.save()
        self.podcast3.save()

        self.episode1 = Episode(podcast=self.podcast1.get_id(),
                urls = ['http://example.com/episode1.mp3'])
        self.episode2 = Episode(podcast=self.podcast2.get_id(),
                urls = ['http://example.com/episode1.mp3'])
        self.episode3 = Episode(podcast=self.podcast3.get_id(),
                urls = ['http://example.com/media.mp3'])


        self.episode1.save()
        self.episode2.save()
        self.episode3.save()

        self.podcast2.group_with(self.podcast3, 'My Group', 'Feed1', 'Feed2')

        self.user = User(username='test-merge-group')
        self.user.email = 'test@example.com'
        self.user.set_password('secret!')
        self.user.save()


    def test_merge_podcasts(self):

        podcast1 = podcast_by_id(self.podcast1.get_id())
        podcast2 = podcast_by_id(self.podcast2.get_id())
        podcast3 = podcast_by_id(self.podcast3.get_id())

        # assert that the podcasts are actually grouped
        self.assertEqual(podcast2._id, podcast3._id)
        self.assertNotEqual(podcast2.get_id(), podcast2._id)
        self.assertNotEqual(podcast3.get_id(), podcast3._id)

        # Create additional data that will be merged
        state1 = episode_state_for_user_episode(self.user, self.episode1)
        state2 = episode_state_for_user_episode(self.user, self.episode2)

        action1 = EpisodeAction(action='play',
                timestamp=datetime.utcnow(),
                upload_timestamp=get_timestamp(datetime.utcnow()))
        action2 = EpisodeAction(action='download',
                timestamp=datetime.utcnow(),
                upload_timestamp=get_timestamp(datetime.utcnow()))

        add_episode_actions(state1, [action1])
        add_episode_actions(state2, [action2])

        # copy of the object
        episode2 = episode_by_id(self.episode2._id)

        # decide which episodes to merge
        groups = [(0, [self.episode1, self.episode2])]
        counter = Counter()

        pm = PodcastMerger([podcast2, podcast1], counter, groups)
        pm.merge()

        state1 = episode_state_for_user_episode(self.user, self.episode1)
        state2 = episode_state_for_user_episode(self.user, episode2)

        self.assertIn(action1, state1.actions)
        self.assertIn(action2, state1.actions)
        self.assertEqual(state2._id, None)

        episode1 = episode_by_id(self.episode1._id)

        # episode2 has been merged into episode1, so it must contain its
        # merged _id
        self.assertEqual(episode1.merged_ids, [episode2._id])



    def tearDown(self):
        self.podcast2.delete()
        self.episode1.delete()

        #self.podcast2.delete()
        #self.episode2.delete()

        self.user.delete()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MergeTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MergeGroupTests))
    return suite
