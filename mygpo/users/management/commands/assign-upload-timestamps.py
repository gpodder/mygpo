from datetime import datetime

from couchdbkit import Consumer

from mygpo.maintenance.management.changescmd import ChangesCommand
from mygpo.decorators import repeat_on_conflict
from mygpo.users.models import EpisodeUserState


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
        return bool(action.upload_timestamp)


    @staticmethod
    def set_upload_timestamp(action, default=datetime.utcnow()):
        if not action.upload_timestamp:
            action.upload_timestamp = min(action.timestamp, default)

        try:
            action.validate_time_values()
        except:
            return None

        return action


    @repeat_on_conflict(['state'])
    def update_state(self, state):
        actions = filter(None, map(self.set_upload_timestamp, state.actions))
        state.actions = []
        state.add_actions(actions)
        state.save()

    def get_db(self):
        return EpisodeUserState.get_db()
