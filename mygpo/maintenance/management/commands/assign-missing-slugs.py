from django.core.management.base import BaseCommand

from mygpo.core.slugs import PodcastSlug, EpisodeSlug, \
         PodcastsMissingSlugs, EpisodesMissingSlugs
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress


class Command(BaseCommand):


    def handle(self, *args, **options):

        podcasts = PodcastsMissingSlugs()
        total = len(podcasts)
        for n, podcast in enumerate(podcasts):
            slug = PodcastSlug(podcast).get_slug()
            if slug:
                self.update_obj(obj=podcast, slug=slug)
            progress(n+1, total)


        episodes = EpisodesMissingSlugs()
        total = len(episodes)
        for n, episode in enumerate(episodes):
            slug = EpisodeSlug(episode).get_slug()
            if slug:
                self.update_obj(obj=episode, slug=slug)
            progress(n+1, total)


    @repeat_on_conflict(['obj'])
    def update_obj(self, obj, slug):
        obj.slug = slug
        obj.save()
