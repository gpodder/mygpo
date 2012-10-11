import time
import urllib2
from optparse import make_option

from mygpo.decorators import repeat_on_conflict
from mygpo.core.models import Podcast
from mygpo.data import delicious
from mygpo.maintenance.management.podcastcmd import PodcastCommand
from mygpo.db.couchdb.podcast import podcast_by_id


SOURCE = 'delicious'

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
                f = urllib2.urlopen(p.link)
            except urllib2.HTTPError:
                continue

            tags = delicious.get_tags(f.url)

            self.update(podcast=p, tags=tags)


    @repeat_on_conflict(['podcast'], reload_f=lambda x: podcast_by_id(x.get_id()))
    def update(self, podcast, tags):
        podcast.tags[SOURCE] = tags
        podcast.save()
