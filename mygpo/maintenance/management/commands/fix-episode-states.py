from couchdbkit import Consumer

from mygpo.maintenance.management.changescmd import ChangesCommand
from mygpo.core.models import Episode, Podcast, MergedIdException
from mygpo.decorators import repeat_on_conflict
from mygpo.users.models import EpisodeUserState


class Command(ChangesCommand):
    """ Fixes broken references in episode state objects """


    def __init__(self):
        self.podcasts = {}
        self.episodes = {}


    def handle_obj(self, seq, obj, actions):

        # Podcasts
        if not state.podcast in self.podcasts:

            try:
                podcast = Podcast.get(state.podcast, current_id=True)

            except MergedIdException as ex:
                self.podcasts[state.podcast] = ex.current_id

            if podcast:
                self.podcasts[state.podcast] = True

            else:
                if not state.podcast_ref_url:
                    return

                actions['fetch-podcast'] += 1
                podcast = Podcast.for_url(state.podcast_ref_url,create=True)
                self.podcasts[state.podcast] = podcast.get_id()

        if isinstance(self.podcasts.get(state.podcast, False), basestring):
            actions['update-podcast'] += 1
            self.update_podcast(state=state,
                    podcast_id = self.podcasts[state.podcast])



        # Episodes
        if not state.episode in self.episodes:

            try:
                episode = Episode.get(state.episode, current_id=True)

            except MergedIdException as ex:
                self.episodes[state.episode] = ex.current_id

            if episode:
                self.episodes[state.episode] = True

            else:
                if not state.ref_url:
                    return

                actions['fetch-episode'] += 1
                episode = Episode.for_podcast_id_url(state.podcast,
                    state.ref_url, create=True)
                self.episodes[state.episode] = episode._id

        if isinstance(self.episodes.get(state.episode, False), basestring):
            actions['update-episode'] += 1
            self.update_episode(state=state,
                    episode_id = self.episodes[state.episode])



    @repeat_on_conflict(['state'])
    def update_episode(self, state, episode_id):
        state.episode = episode_id
        state.save()

    @repeat_on_conflict(['state'])
    def update_podcast(self, state, podcast_id):
        state.podcast = podcast_id
        state.save()


    def get_objects(self, db, since=0, limit=100):
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


    def get_db(self):
        return EpisodeUserState.get_db()

    def get_status_id(self):
        return 'fix-episode-states-status'

    def get_command_name(self):
        return 'Fix-Episode-States'
