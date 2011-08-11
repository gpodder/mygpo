from django.core.management.base import BaseCommand

from mygpo.core.models import Podcast
from mygpo.core.slugs import PodcastSlug, EpisodeSlug, \
         PodcastsMissingSlugs, EpisodesMissingSlugs, assign_podcast_slug
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress


class Command(BaseCommand):


    def handle(self, *args, **options):

        podcasts = PodcastsMissingSlugs()
        total = len(podcasts)
        for n, podcast in enumerate(podcasts):
            assign_podcast_slug(podcast)
            progress(n+1, total)


        episodes = EpisodesMissingSlugs()
        total = len(episodes)
        podcast = None
        common_title = None

        for n, episode in enumerate(episodes):

            if podcast is None or podcast.get_id() != episode.podcast:
                podcast = Podcast.get(episode.podcast)
                common_title = podcast.get_common_episode_title()

            slug = EpisodeSlug(episode, common_title).get_slug()
            if slug:
                self.update_obj(obj=episode, slug=slug)

            progress(n+1, total)


    @repeat_on_conflict(['obj'])
    def update_obj(self, obj, slug):
        obj.slug = slug
        obj.save()
