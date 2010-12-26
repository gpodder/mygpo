from datetime import datetime

from django.core.management.base import BaseCommand

from mygpo.core import models
from mygpo.api.models import Podcast
from mygpo.utils import progress


class Command(BaseCommand):

    def handle(self, *args, **options):

        started = datetime.now()
        entries = models.Podcast.view('core/podcasts_by_oldid')
        total = entries.total_rows

        for n, entry in enumerate(entries):
            p = Podcast.objects.get(id=entry.oldid)
            data = models.SubscriberData(
                timestamp        = started,
                subscriber_count = max(0, p.subscriber_count()),
                )
            entry.subscribers.append(data)
            entry.save()

            progress(n, total)
