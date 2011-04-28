from django.core.management.base import BaseCommand

from mygpo.core.models import Episode
from mygpo.users.models import EpisodeUserState
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress, multi_request_view


class Command(BaseCommand):
    """
    Podcast-Ids are used to directly reference the Podcast that the Episode of
    an Episode state belongs to. However, they have not been set in early
    migration code. This command is used to add them for previously migrated
    objects.
    """

    def handle(self, *args, **options):

        e_states = multi_request_view(EpisodeUserState,
            'users/episode_states_by_user_episode', include_docs=True)
        total = EpisodeUserState.count()

        for n, e_state in enumerate(e_states):
            episode = Episode.get(e_state.episode)
            self.set_podcast_id(e_state=e_state, podcast_id=episode.podcast)

            progress(n+1, total)


    @repeat_on_conflict(['e_state'])
    def set_podcast_id(self, e_state, podcast_id):
        e_state.podcast = podcast_id
        e_state.save()
