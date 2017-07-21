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
import uuid
from datetime import datetime

from django.test import TestCase

from mygpo.podcasts.models import Podcast
from mygpo.directory.views import ToplistView


class ToplistTests(unittest.TestCase):
    """ Test podcast and episode toplists """

    def test_toplist_languages(self):
        """ Test the all_languages method of the toplists """
        languages = ['de', 'de_AT', 'en']
        for lang in languages:
            Podcast.objects.create(id=uuid.uuid1(),
                                   created=datetime.utcnow(),
                                   language=lang,
                                )

        view = ToplistView()
        all_langs = view.all_languages()
        self.assertEqual(all_langs, {'de': 'Deutsch', 'en': 'English'})
