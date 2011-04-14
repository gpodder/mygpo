from django.core.management.base import BaseCommand

from mygpo.core.slugs import PodcastSlug, PodcastsMissingSlugs
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress


class Command(BaseCommand):


    def handle(self, *args, **options):

        podcasts = PodcastsMissingSlugs()
        total = len(podcasts)
        for n, podcast in enumerate(podcasts):
            slug = PodcastSlug(podcast).get_slug()
            if slug:
                self.update_podcast(podcast=podcast, slug=slug)
            progress(n+1, total)


    @repeat_on_conflict(['podcast'])
    def update_podcast(self, podcast, slug):
        podcast.slug = slug
        podcast.save()
