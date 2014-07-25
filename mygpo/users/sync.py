from collections import namedtuple

from couchdbkit.ext.django.schema import *

from mygpo.podcasts.models import Podcast

import logging
logger = logging.getLogger(__name__)


GroupedDevices = namedtuple('GroupedDevices', 'is_synced devices')


def get_grouped_devices(user):
    """ Returns groups of synced devices and a unsynced group """

    from mygpo.users.models import Client
    clients = Client.objects.filter(user=user, deleted=False)\
                            .order_by('-sync_group')

    last_group = object()
    group = None

    for client in clients:
        # check if we have just found a new group
        if last_group != client.sync_group:
            if group != None:
                yield group

            group = GroupedDevices(client.sync_group is not None, [])

        last_group = client.sync_group
        group.devices.append(client)

    # yield remaining group
    yield group


class SyncedDevicesMixin(DocumentSchema):
    """ Contains the device-syncing functionality of a user """

    sync_groups = ListProperty()

    def get_device_sync_group(self, device):
        """ Returns the sync-group Id of the device """

        for n, group in enumerate(self.sync_groups):
            if device.id in group:
                return n

    def get_devices_in_group(self, sg):
        """ Returns the devices in the group with the given Id """

        ids = self.sync_groups[sg]
        return map(self.get_device, ids)


    def sync_group(self, device):
        """ Sync the group of the device """

        group_index = self.get_device_sync_group(device)

        if group_index is None:
            return

        group_state = self.get_group_state(group_index)

        for device in self.get_devices_in_group(group_index):
            sync_actions = self.get_sync_actions(device, group_state)
            self.apply_sync_actions(device, sync_actions)


    def apply_sync_actions(self, device, sync_actions):
        """ Applies the sync-actions to the device """

        from mygpo.db.couchdb.podcast_state import subscribe, unsubscribe
        from mygpo.users.models import SubscriptionException
        add, rem = sync_actions

        podcasts = Podcast.objects.filter(id__in=(add+rem))
        podcasts = {podcast.id: podcast for podcast in podcasts}

        for podcast_id in add:
            podcast = podcasts.get(podcast_id, None)
            if podcast is None:
                continue
            try:
                subscribe(podcast, self, device)
            except SubscriptionException as e:
                logger.warn('Web: %(username)s: cannot sync device: %(error)s' %
                    dict(username=self.username, error=repr(e)))

        for podcast_id in rem:
            podcast = podcasts.get(podcast_id, None)
            if not podcast:
                continue

            try:
                unsubscribe(podcast, self, device)
            except SubscriptionException as e:
                logger.warn('Web: %(username)s: cannot sync device: %(error)s' %
                    dict(username=self.username, error=repr(e)))


    def get_group_state(self, group_index):
        """ Returns the group's subscription state

        The state is represented by the latest actions for each podcast """

        device_ids = self.sync_groups[group_index]
        devices = self.get_devices(device_ids)

        state = {}

        for d in devices:
            actions = dict(d.get_latest_changes())
            for podcast_id, action in actions.items():
                if not podcast_id in state or \
                        action.timestamp > state[podcast_id].timestamp:
                    state[podcast_id] = action

        return state


    def get_sync_actions(self, device, group_state):
        """ Get the actions required to bring the device to the group's state

        After applying the actions the device reflects the group's state """

        sg = self.get_device_sync_group(device)
        if sg is None:
            return [], []

        # Filter those that describe actual changes to the current state
        add, rem = [], []
        current_state = dict(device.get_latest_changes())

        for podcast_id, action in group_state.items():

            # Sync-Actions must be newer than current state
            if podcast_id in current_state and \
               action.timestamp <= current_state[podcast_id].timestamp:
                continue

            # subscribe only what hasn't been subscribed before
            if action.action == 'subscribe' and \
                        (podcast_id not in current_state or \
                         current_state[podcast_id].action == 'unsubscribe'):
                add.append(podcast_id)

            # unsubscribe only what has been subscribed before
            elif action.action == 'unsubscribe' and \
                        podcast_id in current_state and \
                        current_state[podcast_id].action == 'subscribe':
                rem.append(podcast_id)

        return add, rem
