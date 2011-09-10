from datetime import datetime
from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo.core.models import Podcast, SubscriberData
from mygpo.users.models import PodcastUserState
from mygpo.utils import progress
from mygpo.decorators import repeat_on_conflict


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--silent', action='store_true', dest='silent',
        default=False, help="Don't show any output"),
    )

    def handle(self, *args, **options):

        silent = options.get('silent')

        # couchdbkit doesn't preserve microseconds
        started = datetime.utcnow().replace(microsecond=0)

        podcasts = Podcast.all_podcasts()
        total = Podcast.view('core/podcasts_by_oldid', limit=0).total_rows

        for n, podcast in enumerate(podcasts):
            subscriber_count = self.get_subscriber_count(podcast)
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


    @staticmethod
    def get_subscriber_count(podcast):
        db = PodcastUserState.get_db()
        subscriber_sum = 0

        for podcast_id in podcast.get_ids():
            x = db.view('users/subscriptions_by_podcast',
                    startkey    = [podcast_id, None],
                    endkey      = [podcast_id, {}],
                    reduce      = True,
                    group       = True,
                    group_level = 2,
                )
            subscriber_sum += x.count()

        return subscriber_sum
