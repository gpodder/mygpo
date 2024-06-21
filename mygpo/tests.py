import unittest
from utils import normalize_url

class TestNormalizeFeedURL(unittest.TestCase):
    def test_normalize_url(self):
        coverage = [False] * 11
        #     def _init_(self, scheme=None, netloc=None, path=None, query=None, fragment=None):
        # Test branch 0
        url = " "
        self.assertEqual(normalize_url(url, coverage), None)

        # Test branch 1, 2, 4, 6, 8, 10
        url = "yt:SamuelPower"
        self.assertEqual(
            normalize_url(url, coverage),
            "http://www.youtube.com/rss/user/SamuelPower/videos.rss",
        )

        # Test branch 3
        url = "www.youtube.com/rss/user/SamuelPower/videos.rss"
        self.assertEqual(
            normalize_url(url, coverage),
            "http://www.youtube.com/rss/user/SamuelPower/videos.rss",
        )

        # Test branch 5, 7
        url = "feed://@example.com"
        self.assertEqual(normalize_url(url, coverage), "http://example.com/")

        # Test branch 9
        url = "gopher://example.com"
        self.assertEqual(normalize_url(url, coverage), None)
        write_coverage_to_file(
            "/Users/samuelpower/Desktop/MockedSEP/coverage.txt",
            "normalize feed url",
            coverage,
        )
