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
