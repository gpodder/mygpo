from datetime import datetime

from django.core.management.base import BaseCommand

from couchdbkit import ResourceConflict

from mygpo.core.models import Podcast, SubscriberData
from mygpo.users.models import PodcastUserState
from mygpo.utils import progress, multi_request_view
from mygpo.decorators import repeat_on_conflict


class Command(BaseCommand):

    def handle(self, *args, **options):

        started = datetime.now()
        entries = multi_request_view(Podcast, 'core/podcasts_by_oldid', include_docs=True)
        total = Podcast.view('core/podcasts_by_oldid', limit=0).total_rows

        for n, entry in enumerate(entries):
            subscriber_count = self.get_subscriber_count(entry.get_id())
            self.update(entry=entry, started=started, subscriber_count=subscriber_count)
            progress(n, total)


    @repeat_on_conflict(['entry'])
    def update(self, entry, started, subscriber_count):
        data = SubscriberData(
            timestamp        = started,
            subscriber_count = max(0, subscriber_count),
            )
        entry.subscribers.append(data)
        entry.save()


    @staticmethod
    def get_subscriber_count(podcast_id):
        db = PodcastUserState.get_db()
        x = db.view('users/subscriptions_by_podcast',
                startkey = [podcast_id, None],
                endkey   = [podcast_id, {}],
            )
        return x.count()
