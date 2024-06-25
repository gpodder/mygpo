import re
import json

from django.test import TestCase

from . import flickr

import responses

import unittest
from unittest.mock import Mock
from datetime import datetime
from mygpo.data.feeddownloader import EpisodeUpdater
import os

class TestEpisodeUpdater(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mock_episode = Mock()
        cls.mock_podcast = Mock()
        cls.updater = EpisodeUpdater(cls.mock_episode, cls.mock_podcast)

    @classmethod
    def tearDownClass(cls):
        project_root = os.path.abspath(os.path.dirname(__file__))
        coverage_file_path = os.path.join(project_root, '..', 'coverage', 'mohamed', 'EPISODEUPDATER_mark_outdated_coverage.txt')
        write_coverage_to_file(coverage_file_path, "EpisodeUpdater", cls.updater.report_coverage())

    def setUp(self):
        self.updater.branch_coverage = {1: False, 2: False}  # Reset branch coverage before each test

    def test_update_episode(self):
        # Mock data
        parsed_episode = {
            'guid': 'new-guid',
            'description': 'new-description',
            'subtitle': 'new-subtitle',
            'content': 'new-content',
            'link': 'http://new-link.com',
            'released': 1609459200,  # 2021-01-01 00:00:00 UTC
            'author': 'new-author',
            'duration': 3600,
            'files': [{'filesize': 1024, 'mimetype': 'audio/mp3', 'urls': ['http://file-url.com']}],
            'language': 'en',
            'flattr': 'http://flattr-url.com',
            'license': 'CC-BY',
            'title': 'new-title',
        }

        self.updater.update_episode(parsed_episode)

        # Verify attributes
        self.assertEqual(self.mock_episode.guid, 'new-guid')
        self.assertEqual(self.mock_episode.description, 'new-description')
        self.assertEqual(self.mock_episode.subtitle, 'new-subtitle')
        self.assertEqual(self.mock_episode.content, 'new-content')
        self.assertEqual(self.mock_episode.link, 'http://new-link.com')
        self.assertEqual(self.mock_episode.released, datetime.utcfromtimestamp(1609459200))
        self.assertEqual(self.mock_episode.author, 'new-author')
        self.assertEqual(self.mock_episode.duration, 3600)
        self.assertEqual(self.mock_episode.filesize, 1024)
        self.assertEqual(self.mock_episode.language, 'en')
        self.assertEqual(self.mock_episode.flattr_url, 'http://flattr-url.com')
        self.assertEqual(self.mock_episode.license, 'CC-BY')
        self.assertEqual(self.mock_episode.title, 'new-title')
        self.assertTrue(self.mock_episode.save.called)

        self.assertFalse(self.updater.branch_coverage[1])  
        self.assertFalse(self.updater.branch_coverage[2]) 

    def test_mark_outdated(self):
        # Test not outdated
        self.mock_episode.outdated = False
        self.updater.mark_outdated()
        
        print("Test when episode is not outdated")
        self.assertTrue(self.mock_episode.outdated)
        self.assertTrue(self.mock_episode.save.called)
        self.assertTrue(self.updater.branch_coverage[2])
        self.assertFalse(self.updater.branch_coverage[1])

        # Reset 
        self.updater.branch_coverage = {1: False, 2: False}

        # Test outdated
        self.mock_episode.outdated = True
        self.mock_episode.save.reset_mock()  
        result = self.updater.mark_outdated()
        
        print("Test when episode is already outdated")
        self.assertIsNone(result)
        self.assertTrue(self.updater.branch_coverage[1])
        self.assertFalse(self.updater.branch_coverage[2])
        self.assertFalse(self.mock_episode.save.called)  

    def test_report_coverage(self):
        coverage_data = self.updater.report_coverage()
        self.assertIn(1, coverage_data)  
        self.assertIn(2, coverage_data) 

def write_coverage_to_file(filename, method_name, branch_coverage):
    total = len(branch_coverage)
    num_taken = 0
    with open(filename, 'w') as file:
        file.write(f"FILE: {filename}\nMethod: {method_name}\n")
        for (branch, taken) in enumerate(branch_coverage.items()):
            if taken:
                file.write(f"{branch} was taken\n")
                num_taken+=1
            else:
                file.write(f"{branch} was not taken\n")
        file.write("\n")
        coverage_level = num_taken / total * 100
        file.write(f"Total coverage = {coverage_level}%\n")

MEDIUM_URL = "https://farm6.staticflickr.com/5001/1246644888_36863b0856.jpg"

API_RESPONSE = {
    "stat": "ok",
    "sizes": {
        "canblog": 0,
        "size": [
            {
                "source": "https://farm6.staticflickr.com/5001/1234533888_45673b0856_s.jpg",
                "url": "https://www.flickr.com/photos/someuser/135643888/sizes/sq/",
                "media": "photo",
                "height": 75,
                "width": 75,
                "label": "Square",
            },
            {
                "source": MEDIUM_URL,
                "url": "https://www.flickr.com/photos/someuser/3465234888/sizes/m/",
                "media": "photo",
                "height": "500",
                "width": "333",
                "label": "Medium",
            },
        ],
        "candownload": 1,
        "canprint": 0,
    },
}

FLICKR_URL = re.compile(
    r"https://api.flickr.com/services/rest/\?method=flickr.photos.getSizes&api_key=.*photo_id=.*&format=json&nojsoncallback=1"
)


class FlickrTests(TestCase):
    def test_get_sizes(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET, FLICKR_URL, status=200, body=json.dumps(API_RESPONSE)
            )

            sizes = flickr.get_photo_sizes("1235123123")

        self.assertEqual(sizes, API_RESPONSE["sizes"]["size"])

    def test_display_image(self):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET, FLICKR_URL, status=200, body=json.dumps(API_RESPONSE)
            )

            disp_photo = flickr.get_display_photo(
                "https://farm9.staticflickr.com/8747/12346789012_bf1e234567_b.jpg"
            )

        self.assertEqual(disp_photo, MEDIUM_URL)
