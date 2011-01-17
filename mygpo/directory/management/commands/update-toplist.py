from datetime import datetime

from django.core.management.base import BaseCommand

from couchdbkit import ResourceConflict

from mygpo.core import models
from mygpo.api.models import Podcast
from mygpo.utils import progress
from mygpo.decorators import repeat_on_conflict


class Command(BaseCommand):

    def handle(self, *args, **options):

        started = datetime.now()
        entries = models.Podcast.view('core/podcasts_by_oldid').iterator()
        total = models.Podcast.view('core/podcasts_by_oldid', limit=1).total_rows

        for n, entry in enumerate(entries):
            self.update(entry=entry, started=started)
            progress(n, total)


    @repeat_on_conflict('entry')
    def update(self, entry, started):
        try:
            p = Podcast.objects.get(id=entry.oldid)
        except Podcast.DoesNotExist:
            return

        data = models.SubscriberData(
            timestamp        = started,
            subscriber_count = max(0, p.subscriber_count()),
            )
        entry.subscribers.append(data)
        entry.save()
