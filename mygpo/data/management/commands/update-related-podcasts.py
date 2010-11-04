from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo.api.models import Podcast
from mygpo.data.podcast import calc_similar_podcasts
from mygpo.migrate import use_couchdb, get_or_migrate_podcast
from mygpo.utils import progress


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--max', action='store', type='int', dest='max', default=15, help="Maximum number of similar podcasts to calculate for each podcast."),
        )


    @use_couchdb()
    def handle(self, *args, **options):

        max_related = options.get('max')

        podcasts = Podcast.objects.all().order_by('id').only('id')
        total = podcasts.count()

        for (n, podcast) in enumerate(podcasts.iterator()):

            l = calc_similar_podcasts(podcast)[:max_related]
            related = [get_or_migrate_podcast(p).get_id() for (p, c) in l]

            newp = get_or_migrate_podcast(podcast)
            newp.related_podcasts = related
            newp.save()

            progress(n+1, total)
