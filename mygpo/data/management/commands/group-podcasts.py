from django.core.management.base import BaseCommand

from mygpo.core.models import Podcast
from mygpo.db.couchdb.podcast import podcast_for_url


class Command(BaseCommand):
    def handle(self, *args, **options):

        if len(args) != 5:
            print 'Usage: ./manage.py group-podcasts <url1> <url2> <group-name> <name1> <name2>'
            return

        p1_url = args[0]
        p2_url = args[1]
        group_title = args[2]
        myname = args[3]
        othername = args[4]

        p1 = podcast_for_url(p1_url)
        p2 = podcast_for_url(p2_url)

        p1.group_with(p2, group_title, myname, othername)

