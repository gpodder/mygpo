from django.core.management.base import BaseCommand
from mygpo.api.models import Podcast
from mygpo.api.sanitizing import rewrite_podcasts
from mygpo.data import feeddownloader
from optparse import make_option
import datetime

class Command(BaseCommand):

    def handle(self, *args, **options):

        if len(args) == 0:
            urls = []
            for p in Podcast.objects.all():
                if Podcast.objects.filter(url__exact=p.url).exclude(id=p.id).exists():
                    urls.append(p.url)
  
        else:
            urls = args

        for url in urls:
            p = Podcast.objects.filter(url=url).order_by('id')[0]
            for p2 in Podcast.objects.filter(url=url).exclude(id=p.id).order_by('id'):
                print 'merging %s with %s' % (p.id, p2.id)
                rewrite_podcasts(p2, p)
                p2.delete()

