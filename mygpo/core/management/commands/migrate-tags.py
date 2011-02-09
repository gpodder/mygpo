from django.core.management.base import BaseCommand

from mygpo import migrate
from mygpo.utils import progress
from mygpo.decorators import repeat_on_conflict
from mygpo.data.models import PodcastTag
from mygpo.core import models


class Command(BaseCommand):


    def handle(self, *args, **options):

        tags = PodcastTag.objects.order_by('podcast', 'source', 'user')
        total = tags.count()

        podcast = None
        for n, tag in enumerate(tags):
            podcast = migrate.get_or_migrate_podcast(tag.podcast) if (podcast is None or podcast.oldid != tag.podcast.id) else podcast

            if tag.source in ('feed', 'delicious'):
                self.migrate_podcast_tag(podcast, tag)

            elif tag.source == 'user':
                podcast_state = models.PodcastUserState.for_user_podcast(tag.user, podcast)
                self.migrate_user_tag(podcast_state, tag)

            progress(n+1, total)


    @repeat_on_conflict(['podcast'])
    def migrate_podcast_tag(self, podcast, tag):
        if not tag.source in podcast.tags:
            podcast.tags[tag.source] = []
        podcast.tags[tag.source].append(tag.tag)
        podcast.save()


    @repeat_on_conflict(['podcast_state'])
    def migrate_user_tag(self, podcast_state, tag):
        podcast_state.tags.append(tag.tag)
        podcast_state.save()

