from optparse import make_option
from operator import itemgetter

from django.core.management.base import BaseCommand

from mygpo.podcasts.models import Podcast
from mygpo.data.podcast import calc_similar_podcasts
from mygpo.utils import progress
from mygpo.db.couchdb.podcast import all_podcasts, update_related_podcasts


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--max', action='store', type='int', dest='max', default=15, help="Maximum number of similar podcasts to calculate for each podcast."),
        )


    def handle(self, *args, **options):

        get_podcast = itemgetter(0)

        max_related = options.get('max')

        podcasts = all_podcasts()
        total = Podcast.objects.count()

        for (n, podcast) in enumerate(podcasts):

            l = calc_similar_podcasts(podcast)[:max_related]

            related = map(get_podcast, l)

            update_related_podcasts(podcast, related)

            progress(n+1, total)
