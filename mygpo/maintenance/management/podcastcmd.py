from itertools import islice, chain, imap as map
from optparse import make_option
import random

from django.core.management.base import BaseCommand

from mygpo.core.podcasts import individual_podcasts
from mygpo.podcasts.models import Podcast


class PodcastCommand(BaseCommand):
    """ command that operates on a list of podcasts specified by parameters """

    option_list = BaseCommand.option_list + (
        make_option('--toplist', action='store_true', dest='toplist',
            default=False, help="Update all entries from the Toplist."),

        make_option('--update-new', action='store_true', dest='new',
            default=False, help="Update all podcasts with new Episodes"),

        make_option('--max', action='store', dest='max', type='int',
            default=0, help="Set how many feeds should be updated at maximum"),

        make_option('--random', action='store_true', dest='random',
            default=False, help="Update random podcasts, best used with --max"),

        make_option('--next', action='store_true', dest='next',
            default=False, help="Podcasts that are due to be updated next"),
        )



    def get_podcasts(self, *args, **options):
        return chain.from_iterable(self._get_podcasts(*args, **options))


    def _get_podcasts(self, *args, **options):

        max_podcasts = options.get('max')

        if options.get('toplist'):
            yield (p.url for p in self.get_toplist(max_podcasts))

        if options.get('new'):
            query = Podcast.objects.filter(episode__title__isnull=True,
                                           episode__outdated=False)
            podcasts = query.distinct('id')[:max_podcasts]
            random.shuffle(podcasts)
            yield (p.url for p in podcasts)

        if options.get('random'):
            podcasts = Podcast.objects.random()
            yield (p.url for p in individual_podcasts(podcasts))

        if options.get('next'):
            podcasts = Podcast.objects.order_by_next_update()[:max_podcasts]
            yield (p.url for p in podcasts)


        if args:
            yield args

        if not args and not options.get('toplist') and not options.get('new') \
                    and not options.get('random')  and not options.get('next'):
            query = Podcast.objects.order_by('last_update')
            podcasts = query.select_related('urls')[:max_podcasts]
            yield (p.url for p in podcasts)


    def get_toplist(self, max_podcasts=100):
        toplist = Podcast.objects.all().toplist()
        return individual_podcasts(p for i, p in toplist[:max_podcasts])
