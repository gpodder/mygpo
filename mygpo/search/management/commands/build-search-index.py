from django.core.management.base import BaseCommand
from optparse import make_option
from mygpo.search.models import SearchEntry
from mygpo.api.models import ToplistEntry
from mygpo.search.util import podcast_entry, podcast_group_entry

class Command(BaseCommand):

    def handle(self, *args, **options):

        SearchEntry.objects.all().delete()

        toplist = ToplistEntry.objects.all().order_by('-subscriptions')
        for e in toplist:
            entry = None
            if e.podcast_group:
                entry = podcast_group_entry(e.podcast_group, e.subscriptions)

            elif e.podcast:
                entry = podcast_entry(e.podcast, e.subscriptions)

            if entry and entry.text:
                entry.save()

