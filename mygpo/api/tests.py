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

from django.test import TestCase
from django.contrib.auth.models import User
from mygpo.api.models import Device, Podcast, SubscriptionAction

class SyncTest(TestCase):
    def test_sync_actions(self):
        # this test does not yet complete when run as a unit test
        # because django does not set up the views
        u  = User.objects.create(username='u')
        d1 = Device.objects.create(name='d1', type='other', user=u)
        d2 = Device.objects.create(name='d2', type='other', user=u)
        p1 = Podcast.objects.create(title='p1', url='http://p1.com/')
        p2 = Podcast.objects.create(title='p2', url='http://p2.com/')
        p3 = Podcast.objects.create(title='p3', url='http://p3.com/')
        p4 = Podcast.objects.create(title='p4', url='http://p4.com/')

        s1 = SubscriptionAction.objects.create(device=d1, podcast=p1, action='1')
        s2 = SubscriptionAction.objects.create(device=d2, podcast=p2, action='1')
        u2 = SubscriptionAction.objects.create(device=d2, podcast=p2, action='-1')
        s3 = SubscriptionAction.objects.create(device=d1, podcast=p3, action='1')
        s3_= SubscriptionAction.objects.create(device=d2, podcast=p3, action='1')
        s4 = SubscriptionAction.objects.create(device=d2, podcast=p4, action='1')
        u3 = SubscriptionAction.objects.create(device=d2, podcast=p3, action='-1')

	#d1: p1, p3
	#d2: p2, -p2, p3, p4, -p3

        d1.sync_with(d2)

        #d1: -p3, +p4
        #d2: +p1

        sa1 = d1.get_sync_actions()
        sa2 = d2.get_sync_actions()

        self.assertEqual( len(sa1), 2)
        self.assertEqual( len(sa2), 1)

        self.assertEqual( sa1[p4].device, d2)
        self.assertEqual( sa1[p4].podcast, p4)
        self.assertEqual( sa1[p4].action, 1)

        self.assertEqual( sa1[p3].device, d2)
        self.assertEqual( sa1[p3].podcast, p3)
        self.assertEqual( sa1[p3].action, -1)

        self.assertEqual( sa2[p1].device, d1)
        self.assertEqual( sa2[p1].podcast, p1)
        self.assertEqual( sa2[p1].action, 1)



