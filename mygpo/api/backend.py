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

from datetime import timedelta
from collections import defaultdict
from itertools import cycle
from functools import partial

from django.core.cache import cache

from mygpo.data.mimetype import get_type, CONTENT_TYPES
from mygpo.core.models import Podcast, Episode
from mygpo.users.models import EpisodeUserState, Device, DeviceDoesNotExist, \
         PodcastUserState
from mygpo.decorators import repeat_on_conflict
from mygpo.json import json
from mygpo.couchdb import bulk_save_retry


def get_random_picks(languages=None):
    """ Returns random podcasts for the given language """

    languages = languages or ['']

    # get one iterator for each language
    rand_iters = [Podcast.random(lang) for lang in languages]

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



def get_podcast_count_for_language():
    """ Returns a the number of podcasts for each language """

    counts = defaultdict(int)

    db = Podcast.get_db()
    r = db.view('podcasts/by_language',
        reduce = True,
        group_level = 1,
        stale       = 'update_after',
    )

    counts.update( dict( (x['key'][0], x['value']) for x in r) )
    return counts



def get_device(user, uid, user_agent, undelete=True):
    """
    Loads or creates the device indicated by user, uid.

    If the device has been deleted and undelete=True, it is undeleted.
    """

    store_ua = user.settings.get('store_user_agent', True)

    @repeat_on_conflict(['user'])
    def _get(user, uid, undelete):

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

    return _get(user=user, uid=uid, undelete=undelete)


def get_favorites(user):
    favorites = Episode.view('favorites/episodes_by_user',
            key          = user._id,
            include_docs = True,
        )
    return favorites



class BulkSubscribe(object):
    """ Performs bulk subscribe/unsubscribe operations """

    DB = PodcastUserState.get_db()

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
        bulk_save_retry(self.DB, obj_funs)

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
                Podcast.for_url(url, create=True))

        state = podcast.get_user_state(self.user)

        fun = self.operations[op]
        return (state, fun)



    def _subscribe(self, state, device):
        state.subscribe(device)
        return state

    def _unsubscribe(self, state, device):
        state.unsubscribe(device)
        return state
