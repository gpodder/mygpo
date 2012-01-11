from couchdbkit import Consumer

from mygpo.maintenance.management.changescmd import ChangesCommand
from mygpo.decorators import repeat_on_conflict
from mygpo.users.models import EpisodeUserState, PodcastUserState, \
        Suggestions, User

from mygpo import migrate


CLASSES = {}
for cls in (EpisodeUserState, PodcastUserState, Suggestions, ):
    CLASSES[cls._doc_type] = cls


class Command(ChangesCommand):
    """ Fixes broken references in episode state objects """


    def __init__(self):
        self.users = {}


    def handle_obj(self, seq, obj, actions):
        return self._handle_obj(seq, obj=obj, actions=actions)


    @repeat_on_conflict(['obj'])
    def _handle_obj(self, seq, obj, actions):

        if obj.user:
            return

        user = User.for_oldid(obj.user_oldid)
        obj.user = user._id

        obj.save()
        actions['updated'] += 1



    def get_objects(self, db, since=0, limit=100):
        consumer = Consumer(db)

        while True:
            resp = consumer.wait_once(since=since, limit=10,
                    include_docs=True, filter='users/user_objects')

            results = resp['results']

            if not results:
                break

            for res in results:
                doc = res['doc']
                seq = res['seq']
                doc_type = doc['doc_type']
                cls = CLASSES[doc_type]
                yield seq, cls.wrap(doc)

            since = resp['last_seq']


    def get_db(self):
        return EpisodeUserState.get_db()

    def get_status_id(self):
        return 'assign-user-id-status'

    def get_command_name(self):
        return 'Assign-User-Ids'
