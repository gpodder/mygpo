from optparse import make_option
from operator import itemgetter

from django.core.management.base import BaseCommand

from mygpo.decorators import repeat_on_conflict
from mygpo.core.models import Podcast
from mygpo.data.podcast import calc_similar_podcasts
from mygpo.utils import progress


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--max', action='store', type='int', dest='max', default=15, help="Maximum number of similar podcasts to calculate for each podcast."),
        )


    def handle(self, *args, **options):

        get_podcast = itemgetter(0)

        max_related = options.get('max')

        podcasts = Podcast.all_podcasts()
        total = Podcast.view('core/podcasts_by_id', limit=0).total_rows

        for (n, podcast) in enumerate(podcasts):

            l = calc_similar_podcasts(podcast)[:max_related]

            related = map(get_podcast, l)

            @repeat_on_conflict(['podcast'])
            def _update(podcast, related):
                podcast.related_podcasts = related
                podcast.save()

            _update(podcast=podcast, related=related)

            progress(n+1, total)
