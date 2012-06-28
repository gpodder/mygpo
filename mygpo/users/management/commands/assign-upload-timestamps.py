from datetime import datetime

from couchdbkit import Consumer

from mygpo.maintenance.management.changescmd import ChangesCommand
from mygpo.decorators import repeat_on_conflict
from mygpo.users.models import EpisodeUserState
from mygpo.utils import get_timestamp


class Command(ChangesCommand):
    """ Assigns the upload_timestamp to EpisodeActions

    The field has been added in bug 1366 """


    def __init__(self):
        super(Command, self).__init__('assign-upload-timestamps-status',
            'Assign-Upload-Timestamps')
        self.episodes = {}


    def handle_obj(self, seq, doc, actions):

        obj = EpisodeUserState.wrap(doc)

        if all(self.has_upload_timestamp(action) for action in obj.actions):
            return

        self.update_state(state=obj)

        actions['updated'] += 1


    @staticmethod
    def has_upload_timestamp(action):
        return type(action.upload_timestamp) == int


    @staticmethod
    def set_upload_timestamp(action):
        default = datetime.utcnow()

        if not action.upload_timestamp:
            upload_timestamp = min(action.timestamp, default)
            action.upload_timestamp = get_timestamp(upload_timestamp)

        try:
            action.validate_time_values()
        except:
            return None

        return action



    def get_query_params(self):
        return dict(include_docs=True, filter='episode_states/episode_states')


    @repeat_on_conflict(['state'])
    def update_state(self, state):
        actions = filter(None, map(self.set_upload_timestamp, state.actions))
        state.actions = []
        state.add_actions(actions)
        state.save()

    def get_db(self):
        return EpisodeUserState.get_db()
