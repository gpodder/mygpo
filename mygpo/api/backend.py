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

from collections import defaultdict
from functools import partial

from mygpo.core.models import Podcast, Episode
from mygpo.users.models import EpisodeUserState, Device, DeviceDoesNotExist, \
         PodcastUserState
from mygpo.decorators import repeat_on_conflict
from mygpo.couch import bulk_save_retry
from mygpo.json import json
from mygpo.db.couchdb.podcast import podcast_for_url, random_podcasts
from mygpo.db.couchdb.podcast_state import podcast_state_for_user_podcast


def get_random_picks(languages=None):
    """ Returns random podcasts for the given language """

    languages = languages or ['']

    # get one iterator for each language
    rand_iters = [random_podcasts(lang) for lang in languages]

    # cycle through them, removing those that don't yield any more results
    while rand_iters:
        rand_iter = rand_iters.pop(0)

        try:
            podcast = next(rand_iter)
            rand_iters.append(rand_iter)
            yield podcast

        except StopIteration:
            # don't re-add rand_iter
            pass



@repeat_on_conflict(['user'])
def get_device(user, uid, user_agent, undelete=True):
    """
    Loads or creates the device indicated by user, uid.

    If the device has been deleted and undelete=True, it is undeleted.
    """

    store_ua = user.settings.get('store_user_agent', True)

    save = False

    try:
        device = user.get_device_by_uid(uid, only_active=False)

    except DeviceDoesNotExist:
        device = Device(uid=uid)
        user.devices.append(device)
        save = True

    if device.deleted and undelete:
        device.deleted = False
        user.set_device(device)
        save = True

    if store_ua and user_agent and \
            getattr(device, 'user_agent', None) != user_agent:
        device.user_agent = user_agent
        user.set_device(device)
        save = True

    if save:
        user.save()

    return device


class BulkSubscribe(object):
    """ Performs bulk subscribe/unsubscribe operations """

    def __init__(self, user, device, podcasts = {}, actions=None):
        self.user = user
        self.device = device
        self.podcasts = podcasts
        self.actions = actions or []

        self.operations = {
            'subscribe':   partial(self._subscribe,   device=device),
            'unsubscribe': partial(self._unsubscribe, device=device),
        }


    def execute(self):
        """ Executes all added actions in bulk """
        obj_funs = map(self._get_obj_fun, self.actions)
        bulk_save_retry(obj_funs)

        # prepare for another run
        self.actions = []


    def add_action(self, url, op):
        """ Adds a new (un)subscribe action

        url is the podcast url to subscribe to / unsubscribe from
        op is either "subscribe" or "unsubscribe" """
        self.actions.append( (url, op) )


    def _get_obj_fun(self, action):
        url, op = action

        podcast = self.podcasts.get(url,
                podcast_for_url(url, create=True))

        state = podcast_state_for_user_podcast(self.user, podcast)

        fun = self.operations[op]
        return (state, fun)



    def _subscribe(self, state, device):
        state.subscribe(device)
        return state

    def _unsubscribe(self, state, device):
        state.unsubscribe(device)
        return state
