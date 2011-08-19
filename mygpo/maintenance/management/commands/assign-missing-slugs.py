from itertools import takewhile

from django.core.management.base import BaseCommand
from django.conf import settings

from mygpo.core.models import Podcast
from mygpo.core.slugs import PodcastSlug, EpisodeSlug, PodcastGroupSlug, \
         PodcastsMissingSlugs, EpisodesMissingSlugs, \
         PodcastGroupsMissingSlugs, assign_slug
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress, additional_value


class Command(BaseCommand):


    def handle(self, *args, **options):

        groups = PodcastGroupsMissingSlugs()
        total = len(groups)
        for n, group in enumerate(groups):
            assign_slug(group, PodcastGroupSlug)
            progress(n+1, total)


        # only consider podcasts that have enough subscribers
        min_subscribers = settings.PODCAST_SLUG_SUBSCRIBER_LIMIT
        enough_subscribers = lambda p: p.subscriber_count() >= min_subscribers

        podcasts = PodcastsMissingSlugs()
        total = len(podcasts)

        for n, podcast in enumerate(takewhile(enough_subscribers, podcasts)):
            assign_podcast_slug(podcast)
            progress(n+1, total)


        podcast_changed = lambda e, p: e.podcast != pt.get_id()
        get_podcast = lambda e: Podcast.get(e.podcast)

        episodes = EpisodesMissingSlugs()
        total = len(episodes)
        podcast = None
        common_title = None

        episodes = additional_value(episodes, get_podcast, podcast_changed)

        for n, (episode, podcast) in enumerate(episodes):

            if not podcast.slug:
                continue

            slug = EpisodeSlug(episode, common_title).get_slug()
            if slug:
                self.update_obj(obj=episode, slug=slug)

            progress(n+1, total)


    @repeat_on_conflict(['obj'])
    def update_obj(self, obj, slug):
        obj.set_slug(slug)
        obj.save()
