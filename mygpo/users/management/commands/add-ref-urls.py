from django.core.management.base import BaseCommand

from mygpo.core.models import Podcast, Episode
from mygpo.users.models import PodcastUserState, EpisodeUserState
from mygpo.api import models as oldmodels
from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress, multi_request_view


class Command(BaseCommand):
    """
    Reference URLs are used to store the URLs that a client has used to
    reference a certain podcast or episode. However, they have not been set in
    early migration code. This command is used to add them for previously
    migrated objects.
    """

    def handle(self, *args, **options):

        e_states = multi_request_view(EpisodeUserState,
            'users/episode_states_by_user_episode', include_docs=True)
        p_states = multi_request_view(PodcastUserState,
            'users/podcast_states_by_podcast', include_docs=True)

        total = EpisodeUserState.count() + PodcastUserState.count()

        # Set URLs for Episode States
        for n, e_state in enumerate(e_states):
            try:
                episode = Episode.get(e_state.episode)
                podcast = Podcast.get(episode.podcast)
                self.set_episode_urls(e_state=e_state, episode=episode, podcast=podcast)
            except (oldmodels.Episode.DoesNotExist, oldmodels.Podcast.DoesNotExist):
                pass

            progress(n+1, total)


        # Set URLs for Podcast States
        for n, p_state in enumerate(p_states, n):
            try:
                podcast = Podcast.get(p_state.podcast)
                self.set_podcast_url(p_state=p_state, podcast=podcast)
            except oldmodels.Podcast.DoesNotExist:
                pass

            progress(n+1, total)


    @repeat_on_conflict(['e_state'])
    def set_episode_urls(self, e_state, episode, podcast):
        e_state.ref_url = episode.url
        e_state.podcast_ref_url = podcast.url
        e_state.save()

    @repeat_on_conflict(['p_state'])
    def set_podcast_url(self, p_state, podcast):
        p_state.ref_url = podcast.url
        p_state.save()
