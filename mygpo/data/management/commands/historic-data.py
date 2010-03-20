from django.core.management.base import BaseCommand
from mygpo.data.historic import calc_podcast, calc_episode
from mygpo.api.models import Podcast, Episode

class Command(BaseCommand):
    def handle(self, *args, **options):
        max = Podcast.objects.count()
        n=0

        for p in Podcast.objects.all().iterator():
            n+=1
            print '%d / %d: %d - %s' % (n, max, p.id, p)
            calc_podcast(p)

        max = Episode.objects.all()
        n=0
        for e in Episode.objects.all().iterator():
            n+=1
            print '%d / %d: %d - %s' % (n, max, e.id, p)
            calc_episode(e)

