import sys

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo.core.models import Episode
from mygpo.decorators import repeat_on_conflict
from mygpo.users.models import EpisodeUserState
from mygpo.maintenance.merge import merge_episode_states
from mygpo.utils import progress
from mygpo import migrate



class Command(BaseCommand):
    """
    """

    def handle(self, *args, **options):

        states = EpisodeUserState.view('maintenance/incorrect_episode_ids',
                limit=100,
                include_docs=True)

        total = states.total_rows
        moved, merged = 0, 0

        for n, state in enumerate(states.iterator()):
                try:
                    user = User.objects.get(id=state.user_oldid)
                except User.DoesNotExist:
                    state.delete()
                    continue

                podcast = Podcast.for_url(state.podcast_ref_url)
                if not podcast:
                    state.delete()
                    continue

                try:
                    old_episode = Episode.objects.get(podcast=old_podcast, url=state.ref_url)
                except Episode.DoesNotExist:
                    state.delete()
                    continue

        for n, state in enumerate(states):
                user = User.objects.get(id=state.user_oldid)
                episode = Episode.for_podcast_url(state.podcast_ref_url, state.ref_url)
                new_state = episode.get_user_state(user)

                if not new_state._id:
                    self.update_episode(state=state, episode_id=episode._id)
                    moved += 1

                else:
                    self.delete(state=state)
                    self.merge(new_state=new_state, other_state=state)
                    merged += 1

                progress(n+1, total, 'moved: %d, merged: %d' % (moved, merged))


    @repeat_on_conflict(['state'])
    def update_episode(self, state, episode_id):
        state.episode = episode_id
        state.save()


    @repeat_on_conflict(['new_state'])
    def merge(self, new_state, other_state):
        merge_episode_states(new_state, other_state)
        new_state.save()

    @repeat_on_conflict(['state'])
    def delete(self, state):
        state.delete()
