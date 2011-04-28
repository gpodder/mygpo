from datetime import datetime

from django.core.management.base import BaseCommand

from mygpo.core.models import Episode
from mygpo.utils import progress
from mygpo.decorators import repeat_on_conflict


class Command(BaseCommand):

    def handle(self, *args, **options):

        started = datetime.utcnow()
        entries = Episode.all()
        total = Episode.count()

        for n, entry in enumerate(entries):
            listeners = entry.listener_count()
            self.update(entry=entry, listeners=listeners, started=started)
            progress(n+1, total)


    @repeat_on_conflict(['entry'])
    def update(self, entry, listeners, started):
        entry.listeners = listeners
        entry.save()
