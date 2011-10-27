from couchdbkit import Consumer

from mygpo.maintenance.management.changescmd import ChangesCommand
from mygpo.decorators import repeat_on_conflict
from mygpo.users.models import EpisodeUserState
from mygpo.api.models import Device

from mygpo import migrate


class Command(ChangesCommand):
    """ Fixes broken references in episode state objects """


    def __init__(self):
        self.devices = {}
        self.users = {}


    def handle_obj(self, seq, obj, actions):
        return self._handle_obj(seq, obj=obj, actions=actions)


    @repeat_on_conflict(['obj'])
    def _handle_obj(self, seq, obj, actions):
        changed = False

        for action in obj.actions:

            if action.device:
                continue

            if not action.device_oldid in self.devices:
                try:
                    old_device = Device.objects.get(id=action.device_oldid)
                except Device.DoesNotExist:
                    obj.actions.remove(action)
                    continue

                old_user = old_device.user

                user = self.users.get(old_user.id,
                        migrate.get_or_migrate_user(old_user))

                self.users[old_user.id] = user

                device = migrate.get_or_migrate_device(old_device, user)
                device_id = device.id
                self.devices[old_device.id] = device_id

            else:
                device_id = self.devices[action.device_oldid]

            action.device = device_id
            changed = True

        if changed:
            obj.save()
            actions['updated'] += 1



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
        return 'assign-device-id-status'

    def get_command_name(self):
        return 'Assign-Episode-Ids'
