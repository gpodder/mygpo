import unittest
from .utils import normalize_url

class TestNormalizeFeedURL(unittest.TestCase):
    def test_normalize_url(self):
        coverage = [False] * 12
        #     def _init_(self, scheme=None, netloc=None, path=None, query=None, fragment=None):
        # Test branch 0
        url = " "
        self.assertEqual(normalize_url(url, coverage), None)

        # Test branch 1, 2, 3, 5, 7, 9, 11
        # Tests URL is valid, applies URL fix for prefixes, handles withoutscheme (add http://)
        # normalizes empty paths to /, converts feed:// to http://,returns None for invalid URLs
        # and tests invisible branches
        url = "yt:SamuelPower"
        self.assertEqual(
            normalize_url(url, coverage),
            "http://www.youtube.com/rss/user/SamuelPower/videos.rss",
        )

        # Test branch 4
        # Test URL with missing http:// is corrected
        url = "www.youtube.com/rss/user/SamuelPower/videos.rss"
        self.assertEqual(
            normalize_url(url, coverage),
            "http://www.youtube.com/rss/user/SamuelPower/videos.rss",
        )

        # Test branch 6, 8
        # Test feed:// URL is normalized to http://
        url = "feed://@example.com"
        self.assertEqual(normalize_url(url, coverage), "http://example.com/")

        # Test branch 9
        # Test unsupported scheme (gopher://) returns None
        url = "gopher://example.com"
        self.assertEqual(normalize_url(url, coverage), None)
        write_coverage_to_file(
            "coverage/manual_coverage/samuel_normalize_feed_url_cov.txt",
            "normalize_feed_url",
            coverage,
        )


def write_coverage_to_file(filename, method_name, branch_coverage):
    total = len(branch_coverage)
    num_taken = 0
    with open(filename, "w") as file:
        file.write(f"FILE: {filename}\nMethod: {method_name}\n")
        for index, coverage in enumerate(branch_coverage):
            if coverage:
                file.write(f"Branch {index} was taken\n")
                num_taken += 1
            else:
                file.write(f"Branch {index} was not taken\n")
        file.write("\n")
        coverage_level = num_taken / total * 100
        file.write(f"Total coverage = {coverage_level}%\n")
