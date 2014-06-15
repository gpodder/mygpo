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
import uuid
from datetime import datetime, timedelta

from django.test import TestCase

from mygpo.podcasts.models import Podcast


class PodcastTests(unittest.TestCase):
    """ Test podcasts and their properties """

    def test_next_update(self):
        """ Test calculation of Podcast.next_update """
        last_update = datetime(2014, 03, 31, 11, 00)
        update_interval = 123  # hours

        # create an "old" podcast with update-information
        Podcast.objects.create(id=uuid.uuid1().hex,
                               last_update=last_update,
                               update_interval=update_interval,
                               )

        # the podcast should be the next to be updated
        p = Podcast.objects.order_by_next_update().first()

        # assert that the next_update property is calculated correctly
        self.assertEqual(p.next_update,
                         last_update + timedelta(hours=update_interval))


def load_tests(loader, tests, ignore):
    tests.addTest(unittest.TestLoader().loadTestsFromTestCase(PodcastTests))
    return tests
