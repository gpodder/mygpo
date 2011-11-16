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

from django.test import TestCase

from mygpo.core.models import Podcast, Episode
from mygpo.users.models import EpisodeAction, User
from mygpo.maintenance.merge import merge_podcasts


class MergeTests(TestCase):

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

        self.user = User(username='test')
        self.user.save()


    def test_merge_podcasts(self):

        state1 = self.episode1.get_user_state(self.user)
        state2 = self.episode2.get_user_state(self.user)

        action1 = EpisodeAction(action='play', timestamp=datetime.utcnow())
        action2 = EpisodeAction(action='download', timestamp=datetime.utcnow())

        state1.add_actions([action1])
        state2.add_actions([action2])

        state1.save()
        state2.save()

        merge_podcasts(self.podcast1, self.podcast2)

        state1 = self.episode1.get_user_state(self.user)
        state2 = self.episode2.get_user_state(self.user)

        self.assertIn(action1, state1.actions)
        self.assertIn(action2, state1.actions)



    def tearDown(self):
        self.podcast1.delete()
        self.episode1.delete()

        try:
            self.podcast2.delete()
            self.episode2.delete()
        except:
            pass

        self.user.delete()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MergeTests))
    return suite
