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

from django.test import TestCase

import mygpo.utils
from mygpo.users.models import User, Device


class DeviceSyncTests(unittest.TestCase):

    def setUp(self):
        self.user = User(username='test', email='t@example.com')
        self.user.set_password('asdf')
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


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(DeviceSyncTests))
    return suite
