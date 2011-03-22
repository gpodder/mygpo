from datetime import datetime

from django.core.management.base import BaseCommand

from couchdbkit import ResourceConflict

from mygpo.core.models import Podcast, SubscriberData
from mygpo.utils import progress, multi_request_view
from mygpo.decorators import repeat_on_conflict


class Command(BaseCommand):

    def handle(self, *args, **options):

        started = datetime.now()
        entries = multi_request_view(Podcast, 'core/podcasts_by_oldid')
        total = Podcast.view('core/podcasts_by_oldid', limit=0).total_rows

        for n, entry in enumerate(entries):
            self.update(entry=entry, started=started)
            progress(n, total)


    @repeat_on_conflict(['entry'])
    def update(self, entry, started):
        data = SubscriberData(
            timestamp        = started,
            subscriber_count = max(0, entry.subscriber_count()),
            )
        entry.subscribers.append(data)
        entry.save()
