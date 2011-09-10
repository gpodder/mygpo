from itertools import takewhile

from django.core.management.base import BaseCommand
from django.conf import settings

from mygpo.core.slugs import PodcastSlug, PodcastGroupSlug, \
         PodcastsMissingSlugs, \
         PodcastGroupsMissingSlugs, assign_slug
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress


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
            assign_slug(podcast, PodcastSlug)
            progress(n+1, total)


    @repeat_on_conflict(['obj'])
    def update_obj(self, obj, slug):
        obj.set_slug(slug)
        obj.save()
