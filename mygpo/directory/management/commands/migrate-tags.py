from optparse import make_option
from django.core.management.base import BaseCommand

from mygpo import migrate
from mygpo.utils import progress
from mygpo.decorators import repeat_on_conflict
from mygpo.data.models import PodcastTag
from mygpo.users.models import PodcastUserState


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--source', action='store', type="string", dest='source', default=0, help="Source from which Podcast-Tags should be migrated."),
    )

    def handle(self, *args, **options):

        tags = PodcastTag.objects.order_by('podcast', 'source', 'user')

        src = options.get('source', None)
        if src:
            tags = tags.filter(source=src)

        total = tags.count()

        podcast = None
        for n, tag in enumerate(tags):

            try:
                p = tag.podcast
            except Podcast.DoesNotExist:
                continue

            podcast = migrate.get_or_migrate_podcast(p) if (podcast is None or podcast.oldid != p.id) else podcast

            if tag.source in ('feed', 'delicious'):
                self.migrate_podcast_tag(podcast=podcast, tag=tag)

            elif tag.source == 'user':
                podcast_state = PodcastUserState.for_user_podcast(tag.user, podcast)
                self.migrate_user_tag(podcast_state=podcast_state, tag=tag)

            progress(n+1, total)


    @repeat_on_conflict(['podcast'])
    def migrate_podcast_tag(self, podcast, tag):
        if not tag.source in podcast.tags:
            podcast.tags[tag.source] = []
        podcast.tags[tag.source] = list(set(podcast.tags[tag.source] + [tag.tag]))
        podcast.save()


    @repeat_on_conflict(['podcast_state'])
    def migrate_user_tag(self, podcast_state, tag):
        podcast_state.tags = list(set(podcast_state.tags + [tag.tag]))
        podcast_state.save()

