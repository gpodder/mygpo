from mygpo.users.models import EpisodeUserState
from mygpo.maintenance.management.changescmd import ChangesCommand
from mygpo.db.couchdb import get_userdata_database
from mygpo.db.couchdb.episode import episode_by_id, set_episode_listeners
from mygpo.db.couchdb.episode_state import episode_listener_count


class Command(ChangesCommand):

    def __init__(self):
        super(Command, self).__init__('episode-toplist-status',
                'Episode-Toplist-Update')

    def handle_obj(self, seq, doc, actions):
        state = EpisodeUserState.wrap(doc)

        episode = episode_by_id(state.episode)

        if not episode:
            actions['missing'] += 1
            return

        listeners = episode_listener_count(episode)
        updated = set_episode_listeners(episode, listeners)
        actions['updated'] += int(updated)


    def get_query_params(self):
        return dict(include_docs=True, filter='episode_states/has_play_events')

    def get_db(self):
        return get_userdata_database()
