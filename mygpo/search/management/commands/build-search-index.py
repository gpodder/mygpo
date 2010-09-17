from django.core.management.base import BaseCommand
from optparse import make_option
from mygpo.search.models import SearchEntry
from mygpo.api.models import ToplistEntry

class Command(BaseCommand):

    def handle(self, *args, **options):

        SearchEntry.objects.all().delete()

        toplist = ToplistEntry.objects.all()
        for e in toplist:
            entry = None
            if e.podcast_group:
                entry = SearchEntry.from_object(e.podcast_group, e.subscriptions)

            elif e.podcast:
                entry = SearchEntry.from_object(e.podcast, e.subscriptions)

            if entry and entry.text:
                entry.save()

