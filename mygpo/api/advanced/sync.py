#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

from mygpo.api.basic_auth import require_valid_user, check_username
from django.http import HttpResponseBadRequest
from mygpo.api.httpresponse import JsonResponse
from django.shortcuts import get_object_or_404
from mygpo.api.models import Device
from django.views.decorators.csrf import csrf_exempt
from mygpo.decorators import allowed_methods
from mygpo import migrate

try:
    import simplejson as json
except ImportError:
    import json


@csrf_exempt
@require_valid_user
@check_username
@allowed_methods(['GET', 'POST'])
def main(request, username):
    """ API Endpoint for Device Synchronisation """

    user = migrate.get_or_migrate_user(request.user)

    if request.method == 'GET':
        return JsonResponse(get_sync_status(user))

    else:
        try:
            actions = json.loads(request.raw_post_data)
        except Exception as e:
            return HttpResponseBadRequest(str(e))

        synclist = actions.get('synchronize', [])
        stopsync = actions.get('stop-synchronize', [])

        try:
            update_sync_status(user, synclist, stopsync)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        return JsonResponse(get_sync_status(user))



def get_sync_status(user):
    """ Returns the current Device Sync status """

    sync_groups = []
    unsynced = []

    for group in user.get_grouped_devices():
        uids = [device.uid for device in group.devices]

        if group.is_synced:
            sync_groups.append(uids)

        else:
            unsynced = uids

    return {
        'synchronized': sync_groups,
        'not-synchronized': unsynced
    }



def update_sync_status(user, synclist, stopsync):
    """ Updates the current Device Sync status

    Synchronisation between devices can be set up and stopped.  Devices are
    identified by their UIDs. Unknown UIDs cause errors, no new devices are
    created. """

    for devlist in synclist:

        if len(devlist) <= 1:
            raise ValueError('at least two devices are needed to sync')

        # Setup all devices to sync with the first in the list
        uid = devlist[0]
        dev = user.get_device_by_uid(uid)

        for other_uid in devlist[1:]:
            other = user.get_device_by_uid(other_uid)
            user.sync_devices(dev, other)


    for uid in stopsync:
        dev = user.get_device_by_uid(uid)
        try:
            user.unsync_device(dev)
        except ValueError:
            # if all devices of a sync-group are un-synced,
            # the last one will raise a ValueError, because it is no longer
            # being synced -- we just ignore it
            pass

    user.save()
