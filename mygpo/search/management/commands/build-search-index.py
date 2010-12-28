from django.core.management.base import BaseCommand
from mygpo.search.models import SearchEntry
from mygpo.api.models import Podcast, PodcastGroup
from mygpo.core import models

class Command(BaseCommand):

    def handle(self, *args, **options):

        objects = models.Podcast.all_podcasts_groups()
        SearchEntry.objects.all().delete()

        oldobjects = ((o.get_old_obj(), o.subscriber_count()) for o in objects)

        for oldobj, subscribers in oldobjects:
            entry = SearchEntry.from_object(oldobj, subscribers)

            if entry and entry.text:
                entry.save()

