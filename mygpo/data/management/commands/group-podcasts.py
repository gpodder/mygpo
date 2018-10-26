from django.core.management.base import BaseCommand

from mygpo.podcasts.models import Podcast


def pairwise(t):
    it = iter(t)
    return zip(it, it)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('title')
        parser.add_argument('url1')
        parser.add_argument('name1')
        parser.add_argument('url2')
        parser.add_argument('name2')

    def handle(self, *args, **options):
        p1_url = options['url1']
        p2_url = options['url2']
        group_title = options['title']
        myname = options['name1']
        othername = options['name2']

        p1 = Podcast.objects.get(urls__url=p1_url)
        p2 = Podcast.objects.get(urls__url=p2_url)

        p1.group_with(p2, group_title, myname, othername)
