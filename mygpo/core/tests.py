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
from mygpo.core.models import Episode


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
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(UnifySlugTests))
    return suite
