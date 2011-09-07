from optparse import make_option

from couchdbkit import Consumer

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from mygpo.core.models import Episode, Podcast
from mygpo.decorators import repeat_on_conflict
from mygpo.users.models import EpisodeUserState
from mygpo.maintenance.merge import merge_episode_states
from mygpo.utils import progress, multi_request_view
from mygpo import migrate

try:
    from collections import Counter
except ImportError:
    from mygpo.counter import Counter


class Command(BaseCommand):
    """ Fixes broken references in episode state objects """


    option_list = BaseCommand.option_list + (
            make_option('--since', action='store', type=int, dest='since',
            default=0, help="Where to start the operation"),
        )


    def handle(self, *args, **options):

        db = EpisodeUserState.get_db()
        since = options.get('since')
        total = db.info()['update_seq']

        states = self.get_states(db, since)
        podcasts = {}
        episodes = {}
        actions = Counter()

        for n, state in states:

            # Podcasts
            if not state.podcast in podcasts:

                podcast = Podcast.get(state.podcast)

                if podcast:
                    podcasts[state.podcast] = True

                else:
                    if not state.podcast_ref_url:
                        continue

                    actions['fetch-podcast'] += 1
                    podcast = Podcast.for_url(state.podcast_ref_url,create=True)
                    podcasts[state.podcast] = podcast.get_id()

            if isinstance(podcasts.get(state.podcast, False), basestring):
                actions['update-podcast'] += 1
                self.update_podcast(state=state,
                        podcast_id=podcasts[state.podcast])



            # Episodes
            if not state.episode in episodes:

                episode = Episode.get(state.episode)

                if episode:
                    episodes[state.episode] = True

                else:
                    if not state.ref_url:
                        continue

                    actions['fetch-episode'] += 1
                    episode = Episode.for_podcast_id_url(state.podcast,
                        state.ref_url, create=True)
                    episodes[state.episode] = episode._id

            if isinstance(episodes.get(state.episode, False), basestring):
                actions['update-episode'] += 1
                self.update_episode(state=state,
                        episode_id=episodes[state.episode])


            status_str = ', '.join('%s: %d' % x for x in actions.items())
            progress(n, total, status_str)


    @repeat_on_conflict(['state'])
    def update_episode(self, state, episode_id):
        state.episode = episode_id
        state.save()

    @repeat_on_conflict(['state'])
    def update_podcast(self, state, podcast_id):
        state.podcast = podcast_id
        state.save()


    @staticmethod
    def get_states(db, since=0, limit=100):
        consumer = Consumer(db)

        while True:
            resp = consumer.wait_once(since=since, limit=limit,
                    include_docs=True, filter='users/episode_states')

            results = resp['results']

            if not results:
                break

            for res in results:
                doc = res['doc']
                seq = res['seq']
                yield seq, EpisodeUserState.wrap(doc)

            since = resp['last_seq']
