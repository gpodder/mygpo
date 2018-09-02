from itertools import islice
import traceback
from optparse import make_option

from mygpo.maintenance.management.podcastcmd import PodcastCommand
from mygpo.data.feeddownloader import update_podcasts

import socket
socket.setdefaulttimeout(300)

import logging
logger = logging.getLogger(__name__)


class Command(PodcastCommand):

    def add_arguments(self, parser):

        super().add_arguments(parser)
        parser.add_argument('--list-only', action='store_true', dest='list',
            default=False, help="Don't update anything, just list podcasts "),


    def handle(self, *args, **options):

        queue = self.get_podcasts(*args, **options)

        max_podcasts = options.get('max')
        if max_podcasts:
            queue = islice(queue, 0, max_podcasts)

        if options.get('list'):
            for podcast in queue:
                logger.info('Podcast %s', podcast)

        else:
            logger.info('Updating podcasts...')

            for podcast in update_podcasts(queue):
                logger.info('Updated podcast %s', podcast)
