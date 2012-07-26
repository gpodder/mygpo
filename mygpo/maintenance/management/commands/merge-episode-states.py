from optparse import make_option

from django.core.management.base import BaseCommand

from mygpo.utils import progress, multi_request_view
from mygpo.users.models import EpisodeUserState
from mygpo.counter import Counter
from mygpo.maintenance.merge import merge_episode_states


class Command(BaseCommand):
    """ Merge duplicate EpisodeUserState documents """

    option_list = BaseCommand.option_list + (
        make_option('--skip', action='store', type=int, dest='skip', default=0,
           help="Number of states to skip"),
    )

    def handle(self, *args, **options):

        skip = options.get('skip')
        total = EpisodeUserState.view('episode_states/by_user_episode',
                limit=0,
            ).total_rows
        states = multi_request_view(EpisodeUserState,
                'episode_states/by_user_episode',
                limit=1000,
                include_docs=True,
                skip=skip,
            )
        actions = Counter()

        prev = next(states)

        for n, state in enumerate(states, skip):

            if prev._id == state._id:
                continue

            if prev.user == state.user and prev.episode == state.episode:
                merge_episode_states(prev, state)
                actions['merged'] += 1

            else:
                prev = state

            status_str = ', '.join('%s: %d' % x for x in actions.items())
            progress(n+1, total, status_str)
