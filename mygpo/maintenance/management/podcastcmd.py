from itertools import islice, chain, imap as map
from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo.core.models import Podcast, PodcastGroup
from mygpo.directory.toplist import PodcastToplist


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
        )



    def get_podcasts(self, *args, **options):
        return chain.from_iterable(self._get_podcasts(*args, **options))


    def _get_podcasts(self, *args, **options):
        if options.get('toplist'):
            yield self.get_toplist()

        if options.get('new'):
            yield self.get_podcast_with_new_episodes()

        if options.get('random'):
            yield Podcast.random()


        get_podcast = lambda url: Podcast.for_url(url, create=True)
        yield map(get_podcast, args)

        if not args and not options.get('toplist') and not options.get('new') \
                    and not options.get('random'):
           yield Podcast.by_last_update()



    def get_podcast_with_new_episodes(self):
        db = Podcast.get_db()
        res = db.view('episodes/need_update',
                group_level = 1,
                reduce      = True,
            )

        for r in res:
            podcast_id = r['key']
            podcast = Podcast.get(podcast_id)
            if podcast:
                yield podcast


    def get_toplist(self):
        toplist = PodcastToplist()
        for oldindex, obj in toplist[:100]:
            if isinstance(obj, Podcast):
                yield obj
            elif isinstance(obj, PodcastGroup):
                for p in obj.podcasts:
                    yield p

