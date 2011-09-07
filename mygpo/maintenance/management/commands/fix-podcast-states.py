from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo.core.models import Podcast
from mygpo.decorators import repeat_on_conflict
from mygpo.users.models import PodcastUserState
from mygpo.maintenance.merge import merge_podcast_states
from mygpo.utils import progress, multi_request_view

try:
    from collections import Counter
except ImportError:
    from mygpo.counter import Counter


class Command(BaseCommand):
    """ Fixes broken references in podcast state objects """


    option_list = BaseCommand.option_list + (
            make_option('--since', action='store', type=int, dest='since',
            default=0, help="Where to start the operation"),
        )


    def handle(self, *args, **options):

        db = PodcastUserState.get_db()
        since = options.get('since')
        total = total = db.view('users/podcast_states_by_user',
                    limit = 0,
                ).total_rows

        states = self.get_states(db, since)
        podcasts = {}
        actions = Counter()

        for n, state in states:

            # Podcasts
            if not state.podcast in podcasts:

                podcast = Podcast.get(state.podcast)

                if podcast:
                    podcasts[state.podcast] = True

                else:
                    if not state.ref_url:
                        continue

                    actions['fetch'] += 1
                    podcast = Podcast.for_url(state.ref_url,create=True)
                    podcasts[state.podcast] = podcast

            new_p = podcasts.get(state.podcast, False)
            if isinstance(new_p, Podcast):

                try:
                    user = User.objects.get(id=state.user_oldid)
                except User.DoesNotExist:
                    actions['missing user'] += 1
                    state.delete()
                    continue

                # always returns a state
                existing_state = PodcastUserState.for_user_podcast(user, new_p)

                if existing_state._id:
                    actions['merge'] += 1
                    merge_podcast_states(existing_state, state)

                else:
                    actions['rewrite'] += 1
                    self.update_podcast(state=state, podcast=new_p)

            status_str = ', '.join('%s: %d' % x for x in actions.items())
            progress(n, total, status_str)



    @repeat_on_conflict(['state'])
    def update_podcast(self, state, podcast):
        if not state.ref_url:
            state.ref_url = podcast.url
        state.podcast = podcast.get_id()
        state.save()


    @staticmethod
    def get_states(db, since=0, limit=100):

        db = PodcastUserState.get_db()

        total = db.view('users/podcast_states_by_user',
                limit = 0,
            ).total_rows

        r = multi_request_view(PodcastUserState,
                'users/podcast_states_by_user',
                include_docs=True
            )

        return enumerate(r)
