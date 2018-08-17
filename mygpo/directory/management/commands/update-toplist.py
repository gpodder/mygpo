from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo.podcasts.models import Podcast
from mygpo.utils import progress
from mygpo.directory.tasks import update_podcast_subscribers


class Command(BaseCommand):
    """ For each podcast a task is scheduled to update its subscriber count """

    def add_arguments(self, parser):
        parser.add_argument(
            '--silent',
            action='store_true',
            dest='silent',
            default=False,
            help="Don't show any output",
        ),

    def handle(self, *args, **options):

        silent = options.get('silent')

        podcasts = Podcast.objects.all()
        total = podcasts.count_fast()

        for n, podcast in enumerate(podcasts):
            update_podcast_subscribers.delay(podcast.get_id())

            if not silent:
                progress(n, total)
