from django.core.management.base import BaseCommand
from mygpo.api.models import Podcast, Episode
from mygpo.api.sanitizing import rewrite_podcasts, rewrite_episodes

class Command(BaseCommand):

    def handle(self, *args, **options):

        if len(args) == 0:
            podcast_urls = []
            for p in Podcast.objects.only('id', 'url'):
                if Podcast.objects.filter(url__exact=p.url).exclude(id=p.id).exists():
                    print 'found podcast url %s' % p.url
                    podcast_urls.append(p.url)

            episode_ids = []
            for e in Episode.objects.only('id', 'url'):
                if Episode.objects.filter(url__exact=e.url, podcast=e.podcast).exclude(id=e.id).exists():
                    print 'found episode url %s' % e.url
                    episode_ids.append(e.id)

        else:
            pocast_urls = args

        for url in podcast_urls:
            p = Podcast.objects.filter(url=url).order_by('id')[0]
            for p2 in Podcast.objects.filter(url=url).exclude(id=p.id).order_by('id'):
                print 'merging podcast %s with %s' % (p.id, p2.id)
                rewrite_podcasts(p2, p)
                p2.delete()

        for e_id in episode_ids:
            e = Episode.objects.get(id=e_id)
            for e2 in Episode.objects.filter(url=e.url, podcast=e.podcast).exlcude(id=e.id).order_by('id'):
                print 'merging episode %s with %s' % (e.id, e2.id)
                rewrite_episodes(e2, e)
                e2.delete()

