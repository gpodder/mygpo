import time
import urllib.request, urllib.error, urllib.parse
from optparse import make_option

from mygpo.data import delicious
from mygpo.maintenance.management.podcastcmd import PodcastCommand


SOURCE = "delicious"


class Command(PodcastCommand):
    """
    Adds tags from the webservice delicious.com to podcasts

    Podcasts are specified either by URL or the --toplist and --random
    parameter. The delicious webservice is queried for the podcasts' websites.
    The returned tags are added to the podcasts for the 'delicious' source.
    """

    def handle(self, *args, **options):

        fetch_queue = self.get_podcasts()

        for p in fetch_queue:
            if not p or not p.link:
                continue

            # we don't want to spam delicious
            time.sleep(1)

            try:
                f = urllib.request.urlopen(p.link)
            except urllib.error.HTTPError:
                continue

            tags = delicious.get_tags(f.url)

            self.update(podcast=p, tags=tags)

    def update(self, podcast, tags):
        podcast.tags[SOURCE] = tags
        podcast.save()
