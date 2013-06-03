from collections import namedtuple

from couchdbkit.ext.django.schema import *

from mygpo.core.models import Podcast, SubscriptionException
from mygpo.db.couchdb.podcast import podcasts_to_dict

import logging
logger = logging.getLogger(__name__)


GroupedDevices = namedtuple('GroupedDevices', 'is_synced devices')



class SyncedDevicesMixin(DocumentSchema):
    """ Contains the device-syncing functionality of a user """

    sync_groups = ListProperty()


    def get_grouped_devices(self):
        """ Returns groups of synced devices and a unsynced group """

        indexed_devices = dict( (dev.id, dev) for dev in self.active_devices )

        for group in self.sync_groups:

            devices = [indexed_devices.pop(device_id, None) for device_id in group]
            devices = filter(None, devices)
            if not devices:
                continue

            yield GroupedDevices(
                    True,
                    devices
                )

        # un-synced devices
        yield GroupedDevices(
                False,
                indexed_devices.values()
            )


    def sync_devices(self, device1, device2):
        """ Puts two devices in a common sync group"""

        devices = set([device1, device2])
        if not devices.issubset(set(self.devices)):
            raise ValueError('the devices do not belong to the user')

        sg1 = self.get_device_sync_group(device1)
        sg2 = self.get_device_sync_group(device2)

        if sg1 is not None and sg2 is not None:
            # merge sync_groups
            self.sync_groups[sg1].extend(self.sync_groups[sg2])
            self.sync_groups.pop(sg2)

        elif sg1 is None and sg2 is None:
            self.sync_groups.append([device1.id, device2.id])

        elif sg1 is not None:
            self.sync_groups[sg1].append(device2.id)

        elif sg2 is not None:
            self.sync_groups[sg2].append(device1.id)


    def unsync_device(self, device):
        """ Removts the device from its sync-group

        Raises a ValueError if the device is not synced """

        sg = self.get_device_sync_group(device)

        if sg is None:
            raise ValueError('the device is not synced')

        group = self.sync_groups[sg]

        if len(group) <= 2:
            self.sync_groups.pop(sg)

        else:
            group.remove(device.id)


    def get_device_sync_group(self, device):
        """ Returns the sync-group Id of the device """

        for n, group in enumerate(self.sync_groups):
            if device.id in group:
                return n


    def is_synced(self, device):
        return self.get_device_sync_group(device) is not None


    def get_synced(self, device):
        """ Returns the devices that are synced with the given one """

        sg = self.get_device_sync_group(device)

        if sg is None:
            return []

        devices = self.get_devices_in_group(sg)
        devices.remove(device)
        return devices



    def get_sync_targets(self, device):
        """ Returns the devices and groups with which the device can be synced

        Groups are represented as lists of devices """

        sg = self.get_device_sync_group(device)

        for n, group in enumerate(self.get_grouped_devices()):

            if sg == n:
                # the device's group can't be a sync-target
                continue

            elif group.is_synced:
                yield group.devices

            else:
                # every unsynced device is a sync-target
                for dev in group.devices:
                    if not dev == device:
                        yield dev


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

        add, rem = sync_actions

        podcasts = podcasts_to_dict(add + rem)

        for podcast_id in add:
            podcast = podcasts.get(podcast_id, None)
            if podcast is None:
                continue
            try:
                podcast.subscribe(self, device)
            except SubscriptionException as e:
                logger.warn('Web: %(username)s: cannot sync device: %(error)s' %
                    dict(username=self.username, error=repr(e)))

        for podcast_id in rem:
            podcast = podcasts.get(podcast_id, None)
            if not podcast:
                continue

            try:
                podcast.unsubscribe(self, device)
            except SubscriptionException as e:
                logger.warn('Web: %(username)s: cannot sync device: %(error)s' %
                    dict(username=self.username, error=repr(e)))


    def get_group_state(self, group_index):
        """ Returns the group's subscription state

        The state is represented by the latest actions for each podcast """

        device_ids = self.sync_groups[group_index]
        devices = [self.get_device(device_id) for device_id in device_ids]

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
