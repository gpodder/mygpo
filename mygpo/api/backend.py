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
import uuid

from mygpo.podcasts.models import Podcast
from mygpo.users.models import EpisodeUserState, Device, DeviceDoesNotExist, \
         PodcastUserState
from mygpo.decorators import repeat_on_conflict
from mygpo.core.json import json
from mygpo.users.settings import STORE_UA
from mygpo.users.models import Client
from mygpo.db.couchdb import bulk_save_retry, get_userdata_database
from mygpo.db.couchdb.podcast_state import podcast_state_for_user_podcast


def get_device(user, uid, user_agent, undelete=True):
    """
    Loads or creates the device indicated by user, uid.

    If the device has been deleted and undelete=True, it is undeleted.
    """

    store_ua = user.profile.get_wksetting(STORE_UA)

    save = False

    client, created = Client.objects.update_or_create(user=user, uid=uid,
                        defaults = {
                            'id': uuid.uuid1()
                        })

    if client.deleted and undelete:
        client.deleted = False
        save = True

    if store_ua and user_agent and client.user_agent != user_agent:
        client.user_agent = user_agent

    if save:
        client.save()

    return client


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
        udb = get_userdata_database()
        bulk_save_retry(obj_funs, udb)

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
                Podcast.objects.get_or_create_for_url(url))

        state = podcast_state_for_user_podcast(self.user, podcast)

        fun = self.operations[op]
        return (state, fun)



    def _subscribe(self, state, device):
        state.subscribe(device)
        return state

    def _unsubscribe(self, state, device):
        state.unsubscribe(device)
        return state
