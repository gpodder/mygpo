from django.core.management.base import BaseCommand
from mygpo.data.historic import calc_podcast
from mygpo.api.models import Podcast

class Command(BaseCommand):
    def handle(self, *args, **options):
        max = Podcast.objects.count()
        n=0

        for p in Podcast.objects.all().order_by('id').iterator():
            n+=1
            print '%d / %d: %d - %s' % (n, max, p.id, p)
            calc_podcast(p)


