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

import unittest
import doctest
from collections import Counter

from django.test import TestCase
from django.test.utils import override_settings

import mygpo.utils
from mygpo.core.models import Podcast
from mygpo.maintenance.merge import PodcastMerger
from mygpo.api.backend import get_device
from mygpo.users.models import User, Device
from mygpo.db.couchdb.podcast import podcast_for_url
from mygpo.db.couchdb.podcast_state import subscribed_podcast_ids_by_user_id


class DeviceSyncTests(unittest.TestCase):

    def setUp(self):
        self.user = User(username='test')
        self.user.email = 'test@invalid.com'
        self.user.set_password('secret!')
        self.user.save()


    def test_group(self):
        dev1 = Device(uid='d1')
        self.user.devices.append(dev1)

        dev2 = Device(uid='d2')
        self.user.devices.append(dev2)

        group = self.user.get_grouped_devices().next()
        self.assertEquals(group.is_synced, False)
        self.assertIn(dev1, group.devices)
        self.assertIn(dev2, group.devices)


        dev3 = Device(uid='d3')
        self.user.devices.append(dev3)

        self.user.sync_devices(dev1, dev3)

        groups = self.user.get_grouped_devices()
        g1 = groups.next()

        self.assertEquals(g1.is_synced, True)
        self.assertIn(dev1, g1.devices)
        self.assertIn(dev3, g1.devices)

        g2 = groups.next()
        self.assertEquals(g2.is_synced, False)
        self.assertIn(dev2, g2.devices)


        targets = self.user.get_sync_targets(dev1)
        target = targets.next()
        self.assertEquals(target, dev2)


@override_settings(CACHE={})
class UnsubscribeMergeTests(TestCase):
    """ Test if merged podcasts can be properly unsubscribed

    TODO: this test fails intermittently """

    P2_URL = 'http://test.org/podcast/'

    def setUp(self):
        self.podcast1 = Podcast(urls=['http://example.com/feed.rss'])
        self.podcast2 = Podcast(urls=[self.P2_URL])
        self.podcast1.save()
        self.podcast2.save()

        self.user = User(username='test-merge')
        self.user.email = 'test@example.com'
        self.user.set_password('secret!')
        self.user.save()

        self.device = get_device(self.user, 'dev', '')

    def test_merge_podcasts(self):
        self.podcast2.subscribe(self.user, self.device)

        # merge podcast2 into podcast1
        pm = PodcastMerger([self.podcast1, self.podcast2], Counter(), [])
        pm.merge()

        # seems that setting delayed_commit = false in the CouchDB config, as
        # well as a delay here fix the intermittent failures.
        # TODO: further investiation needed
        import time
        time.sleep(2)

        # get podcast for URL of podcast2 and unsubscribe from it
        p = podcast_for_url(self.P2_URL)
        p.unsubscribe(self.user, self.device)

        subscriptions = subscribed_podcast_ids_by_user_id(self.user._id)
        self.assertEqual(0, len(subscriptions))

    def tearDown(self):
        self.podcast1.delete()
        self.user.delete()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(DeviceSyncTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(UnsubscribeMergeTests))
    return suite
