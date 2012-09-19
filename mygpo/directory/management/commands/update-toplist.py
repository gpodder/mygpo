from datetime import datetime
from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo.core.models import Podcast, SubscriberData
from mygpo.couch import get_main_database
from mygpo.utils import progress
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb.podcast import podcast_count, all_podcasts
from mygpo.db.couchdb.podcast_state import podcast_subscriber_count


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--silent', action='store_true', dest='silent',
        default=False, help="Don't show any output"),
    )

    def handle(self, *args, **options):

        silent = options.get('silent')

        # couchdbkit doesn't preserve microseconds
        started = datetime.utcnow().replace(microsecond=0)

        podcasts = all_podcasts()
        total = podcast_count()

        for n, podcast in enumerate(podcasts):
            subscriber_count = podcast_subscriber_count(podcast)
            self.update(podcast=podcast, started=started, subscriber_count=subscriber_count)

            if not silent:
                progress(n, total)


    @repeat_on_conflict(['podcast'])
    def update(self, podcast, started, subscriber_count):

        # We've already updated this podcast
        if started in [e.timestamp for e in podcast.subscribers]:
            return

        data = SubscriberData(
            timestamp        = started,
            subscriber_count = max(0, subscriber_count),
            )

        podcast.subscribers = sorted(podcast.subscribers + [data], key=lambda e: e.timestamp)
        podcast.save()
