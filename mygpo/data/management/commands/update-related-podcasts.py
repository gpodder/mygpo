from django.core.management.base import BaseCommand
from optparse import make_option
from mygpo.api.models import Podcast
from mygpo.data.models import RelatedPodcast
from mygpo.data.podcast import calc_similar_podcasts

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--max', action='store', type='int', dest='max', default=15, help="Maximum number of similar podcasts to calculate for each podcast."),
        )


    def handle(self, *args, **options):

        max_related = options.get('max')

        podcasts = Podcast.objects.all().order_by('id').only('id')

        for podcast in podcasts.iterator():
            print podcast.id, podcast.title

            l = calc_similar_podcasts(podcast)

            RelatedPodcast.objects.filter(ref_podcast=podcast).delete()
            for (p, count) in l[:max_related]:
                RelatedPodcast.objects.create(ref_podcast=podcast, rel_podcast=p, priority=count)

