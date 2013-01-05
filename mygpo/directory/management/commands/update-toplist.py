from datetime import datetime
from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo.core.models import Podcast, SubscriberData
from mygpo.utils import progress
from mygpo.decorators import repeat_on_conflict
from mygpo.db.couchdb.podcast import podcast_count, all_podcasts, podcast_by_id
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


    @repeat_on_conflict(['podcast'], reload_f=lambda p: podcast_by_id(p.get_id()))
    def update(self, subscriber_data, podcast):

        # We've already updated this podcast
        if subscriber_data.timestamp in [e.timestamp for e in podcast.subscribers]:
            return

        podcast.subscribers = sorted(podcast.subscribers + [subscriber_data], key=lambda e: e.timestamp)
        podcast.subscribers = podcast.subscribers[-2:]

        podcast.save()
