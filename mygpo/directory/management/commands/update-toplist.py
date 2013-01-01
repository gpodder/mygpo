from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo.utils import progress
from mygpo.db.couchdb.podcast import podcast_count, all_podcasts
from mygpo.directory.tasks import update_podcast_subscribers


class Command(BaseCommand):
    """ For each podcast a task is scheduled to update its subscriber count """

    option_list = BaseCommand.option_list + (
        make_option('--silent', action='store_true', dest='silent',
        default=False, help="Don't show any output"),
    )

    def handle(self, *args, **options):

        silent = options.get('silent')

        podcasts = all_podcasts()
        total = podcast_count()

        for n, podcast in enumerate(podcasts):
            update_podcast_subscribers.delay(podcast.get_id())

            if not silent:
                progress(n, total)
