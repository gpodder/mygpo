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
from mygpo.core.slugs import get_duplicate_slugs
from mygpo.core.models import Podcast, PodcastGroup, Episode


class PodcastGroupTests(unittest.TestCase):

    def test_group(self):
        self.podcast1 = Podcast(urls=['http://example1.com'])
        self.podcast1.save()

        self.podcast2 = Podcast(urls=['http://example2.com'])
        self.podcast2.save()

        group = self.podcast1.group_with(self.podcast2, 'My Group', 'p1', 'p2')

        self.assertIn(self.podcast1, group.podcasts)
        self.assertIn(self.podcast2, group.podcasts)
        self.assertEquals(len(group.podcasts), 2)
        self.assertEquals(group.title, 'My Group')
        self.assertEquals(self.podcast1.group_member_name, 'p1')
        self.assertEquals(self.podcast2.group_member_name, 'p2')

        # add to group
        self.podcast3 = Podcast(urls=['http://example3.com'])
        self.podcast3.save()

        group = self.podcast1.group_with(self.podcast3, 'My Group', 'p1', 'p3')

        self.assertIn(self.podcast3, group.podcasts)
        self.assertEquals(self.podcast3.group_member_name, 'p3')

        # add group to podcast
        self.podcast4 = Podcast(urls=['http://example4.com'])
        self.podcast4.save()

        group = self.podcast4.group_with(self.podcast1, 'My Group', 'p4', 'p1')

        self.assertIn(self.podcast4, group.podcasts)
        self.assertEquals(self.podcast4.group_member_name, 'p4')



class UnifySlugTests(unittest.TestCase):

    def test_unify(self):

        from mygpo.core.models import Episode
        a = Episode(_id='a', slug='1')
        b = Episode(_id='b', merged_slugs=['1'])
        c = Episode(_id='c', merged_slugs=['1'])

        dups_list = list(get_duplicate_slugs([a, b, c]))

        # only one duplicate slug is reported
        self.assertEquals(len(dups_list), 1)

        slug, dups = dups_list[0]

        self.assertEquals(slug, '1')
        self.assertEquals(len(dups), 2)
        self.assertEquals(dups[0], b)
        self.assertEquals(dups[1], c)
        self.assertEquals(dups, [b, c])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocTestSuite(mygpo.utils))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(PodcastGroupTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(UnifySlugTests))
    return suite
