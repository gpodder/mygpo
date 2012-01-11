from django.core.management.base import BaseCommand

from mygpo.decorators import repeat_on_conflict
from mygpo.utils import progress, multi_request_view
from mygpo.users.models import PodcastUserState, EpisodeUserState


class Command(BaseCommand):
    """
    Moves EpisodeUserStates that were previously in PodcastUserStates into
    their own Documents

    During the migration to CouchDB, episode states have been included in their
    related podcast states documents. However this has proven to result in bad
    performance as the episodes are not always needed but would have to be
    loaded and parsed whenever the podcast state is accessed.
    """


    def handle(self, *args, **options):

        total = PodcastUserState.view('users/podcast_states_by_podcast', limit=0).total_rows
        states = multi_request_view(PodcastUserState, 'users/podcast_states_by_podcast', include_docs=True)

        for n, state in enumerate(states):

            if not 'episodes' in state:
                continue

            sub_total = len(state.episodes)
            for m, (episode_id, episode_state) in enumerate(state.episodes.items()):
                e_state = EpisodeUserState.for_user_episode(
                    state.user, episode_id)

                if e_state:
                    continue

                episode_state.podcast = state.podcast
                episode_state.user = state.user
                episode_state.save()

                progress(n+1, total, '(%d / %d)' % (m, sub_total))

            self.remove_episodes(state=state)

            progress(n+1, total)


    @repeat_on_conflict(['state'])
    def remove_episodes(self, state):
        del state.episodes
        state.save()
