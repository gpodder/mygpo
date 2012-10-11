from couchdbkit.exceptions import ResourceNotFound

from mygpo.users.models import EpisodeUserState
from mygpo.decorators import repeat_on_conflict
from mygpo.maintenance.management.changescmd import ChangesCommand
from mygpo.db.couchdb.episode import episode_by_id
from mygpo.db.couchdb.episode_state import episode_listener_count


class Command(ChangesCommand):

    def __init__(self):
        super(Command, self).__init__('episode-toplist-status',
                'Episode-Toplist-Update')


    def handle_obj(self, seq, doc, actions):
        state = EpisodeUserState.wrap(doc)

        try:
            episode = episode_by_id(state.episode)

        except ResourceNotFound:
            episode = None

        if episode:
            listeners = episode_listener_count(episode)
            updated = self.update(episode=episode, listeners=listeners)
            actions['updated'] += updated

        else:
            actions['missing'] += 1


    @repeat_on_conflict(['episode'])
    def update(self, episode, listeners):
        if episode.listeners == listeners:
            return False

        episode.listeners = listeners
        episode.save()
        return True


    def get_query_params(self):
        return dict(include_docs=True, filter='episode_states/has_play_events')
