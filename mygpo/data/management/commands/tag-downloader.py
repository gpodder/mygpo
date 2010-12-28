from django.core.management.base import BaseCommand
from mygpo.core import models as newmodels
from mygpo.api import models
from mygpo.api import backend
from mygpo.data.models import PodcastTag
from mygpo.data import delicious
from optparse import make_option
import time
import urllib2

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--toplist', action='store_true', dest='toplist', default=False, help="Update all entries from the Toplist."),
	make_option('--max', action='store', dest='max', type='int', default=-1, help="Set how many feeds should be updated at maximum"),

        make_option('--random', action='store_true', dest='random', default=False, help="Update random podcasts, best used with --max option"),
        )


    def handle(self, *args, **options):

        fetch_queue = []

        if options.get('toplist'):
            for subscribers, oldindex, obj in backend.get_toplist(100):
                if isinstance(obj, models.Podcast):
                    fetch_queue.append(obj)
                elif isinstance(obj, models.PodcastGroup):
                    for p in obj.podcasts():
                        fetch_queue.append(p)

        if options.get('random'):
            fetch_queue = models.Podcast.objects.all().order_by('?')

        for url in args:
           try:
                fetch_queue.append(models.Podcast.objects.get(url=url))
           except:
                pass

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

            for tag, count in tags.iteritems():
                try:
                    print ' %s' % tag.decode('utf-8')
                except:
                    pass
                PodcastTag.objects.filter(tag=tag, podcast=p, source='delicious').delete()
                PodcastTag.objects.create(tag=tag, podcast=p, source='delicious', weight=count)

