from itertools import islice
import traceback
from optparse import make_option

from restkit.errors import RequestFailed

from mygpo.maintenance.management.podcastcmd import PodcastCommand
from mygpo.data.feeddownloader import PodcastUpdater

from gevent import monkey
monkey.patch_all()


class Command(PodcastCommand):

    option_list = PodcastCommand.option_list + (
        make_option('--list-only', action='store_true', dest='list',
            default=False, help="Don't update anything, just list podcasts "),
        )


    def handle(self, *args, **options):

        queue = self.get_podcasts(*args, **options)

        max_podcasts = options.get('max')
        if max_podcasts:
            queue = islice(queue, 0, max_podcasts)

        if options.get('list'):
            for podcast in queue:
                print podcast.url

        else:
            print 'Updating podcasts...'

            updater = PodcastUpdater(queue)
            updater.update()
