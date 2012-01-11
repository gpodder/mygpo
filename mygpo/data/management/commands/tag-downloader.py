from django.core.management.base import BaseCommand

from mygpo.decorators import repeat_on_conflict
from mygpo.core.models import Podcast, PodcastGroup
from mygpo.directory.toplist import PodcastToplist
from mygpo.data import delicious
from optparse import make_option
import time
import urllib2

SOURCE = 'delicious'

class Command(BaseCommand):
    """
    Adds tags from the webservice delicious.com to podcasts

    Podcasts are specified either by URL or the --toplist and --random
    parameter. The delicious webservice is queried for the podcasts' websites.
    The returned tags are added to the podcasts for the 'delicious' source.
    """

    option_list = BaseCommand.option_list + (
        make_option('--toplist', action='store_true', dest='toplist', default=False, help="Update all entries from the Toplist."),
        make_option('--max', action='store', dest='max', type='int', default=-1, help="Set how many feeds should be updated at maximum"),
        make_option('--random', action='store_true', dest='random', default=False, help="Update random podcasts, best used with --max option"),
        )


    def handle(self, *args, **options):

        fetch_queue = []

        if options.get('toplist'):
            toplist = PodcastToplist()
            for oldindex, obj in toplist[:100]:
                if isinstance(obj, Podcast):
                    fetch_queue.append(obj)
                elif isinstance(obj, PodcastGroup):
                    fetch_queue.extend(obj.podcasts)

        if options.get('random'):
            podcasts = Podcast.random()
            fetch_queue.extend(podcasts)

        fetch_queue.extend(filter(None, map(Podcast.for_url, args)))

        max = options.get('max', -1)
        if max > 0:
            fetch_queue = fetch_queue[:max]

        for p in fetch_queue:
            if not p or not p.link:
                continue

            # we don't want to spam delicious
            time.sleep(1)

            try:
                f = urllib2.urlopen(p.link)
            except:
                continue

            tags = delicious.get_tags(f.url)

            self.update(podcast=p, tags=tags)


    @repeat_on_conflict(['podcast'], reload_f=lambda x: Podcast.get(x.get_id()))
    def update(self, podcast, tags):
        podcast.tags[SOURCE] = tags
        podcast.save()
