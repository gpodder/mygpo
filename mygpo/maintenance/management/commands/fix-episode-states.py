import sys

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo.decorators import repeat_on_conflict
from mygpo.api.models import Episode, Podcast
from mygpo.users.models import EpisodeUserState
from mygpo.maintenance.merge import merge_episode_states
from mygpo.utils import progress
from mygpo import migrate



class Command(BaseCommand):
    """
    """

    def handle(self, *args, **options):

        states = EpisodeUserState.view('maintenance/incorrect_episode_ids',
                include_docs=True)

        total = states.total_rows

        for n, state in enumerate(states):
                user = User.objects.get(id=state.user_oldid)
                old_podcast = Podcast.objects.get(url=state.podcast_ref_url)
                old_episode = Episode.objects.get(podcast=old_podcast, url=state.ref_url)
                episode = migrate.get_or_migrate_episode(old_episode)
                new_state = episode.get_user_state(user)

                if not new_state._id:
                    self.update_episode(state=state, episode_id=episode._id)

                else:
                    self.delete(state=state)
                    self.merge(new_state=state, other_state=state)

                progress(n+1, total)


    @repeat_on_conflict(['state'])
    def update_episode(self, state, episode_id):
        state.episode = episode_id
        state.save()


    @repeat_on_conflict(['new_state'])
    def merge(self, new_state, other_state):
        merge_episode_states(new_state, state)
        new_state.save()

    @repeat_on_conflict(['state'])
    def delete(self, state):
        state.delete()
