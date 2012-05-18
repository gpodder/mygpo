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
import random

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

    if not languages:
        for podcast in Podcast.random():
            yield podcast

    counts = cache.get('podcast-language-counts')
    if not counts:
        counts = get_podcast_count_for_language()
        cache.set('podcast-language-counts', counts, 60*60)


    # extract positive counts of all languages in language param
    counts = filter(lambda (l, c): l in languages and c > 0, counts.items())

    for lang, count in cycle(counts):
        skip = random.randint(0, count-1)

        for podcast in Podcast.for_language(lang, skip=skip, limit=1):
            yield podcast



def get_podcast_count_for_language():
    """ Returns a the number of podcasts for each language """

    counts = defaultdict(int)

    db = Podcast.get_db()
    r = db.view('core/podcasts_by_language',
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
    favorites = Episode.view('users/favorite_episodes_by_user',
            key          = user._id,
            include_docs = True,
        )
    return favorites



def get_subscription_change_urls(device, since, until, podcasts={}):
    add, rem = device.get_subscription_changes(since, until)

    podcast_ids = add + rem

    # don't fetch existing podcasts
    podcasts = get_to_dict(Podcast, podcast_ids, get_id=Podcast.get_id)

    add_podcasts = filter(None, (podcasts.get(i, None) for i in add))
    rem_podcasts = filter(None, (podcasts.get(i, None) for i in rem))
    add_urls = [ podcast.url for podcast in add_podcasts]
    rem_urls = [ podcast.url for podcast in rem_podcasts]

    return add_urls, rem_urls


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




# keys that are allowed in episode actions
EPISODE_ACTION_KEYS = ('position', 'episode', 'action', 'device', 'timestamp',
                       'started', 'total', 'podcast')


def clean_episode_action_data(action, devices):

    if None in (action.get('podcast', None), action.get('episode', None)):
        return None

    if 'device_id' in action:
        device_id = action['device_id']
        device_uid = devices.get(device_id)
        if device_uid:
            action['device'] = device_uid

        del action['device_id']

    # remove superfluous keys
    for x in action.keys():
        if x not in EPISODE_ACTION_KEYS:
            del action[x]

    # set missing keys to None
    for x in EPISODE_ACTION_KEYS:
        if x not in action:
            action[x] = None

    return action


def podcast_data(obj, domain, scaled_logo_size=64):
    if obj is None:
        raise ValueError('podcast should not be None')

    if isinstance(obj, Podcast):
        podcast = obj
    elif isinstance(obj, PodcastGroup):
        podcast = obj.get_podcast()

    subscribers = obj.subscriber_count()
    last_subscribers = obj.prev_subscriber_count()

    scaled_logo_url = obj.get_logo_url(scaled_logo_size)

    return {
        "url": podcast.url,
        "title": podcast.title,
        "description": podcast.description,
        "subscribers": subscribers,
        "subscribers_last_week": last_subscribers,
        "logo_url": podcast.logo_url,
        "scaled_logo_url": 'http://%s%s' % (domain, scaled_logo_url),
        "website": podcast.link,
        "mygpo_link": 'http://%s%s' % (domain, get_podcast_link_target(obj)),
        }


def episode_data(episode, domain, podcast=None):

    podcast = podcast or Podcast.get(episode.podcast)

    data = {
        "title": episode.title,
        "url": episode.url,
        "podcast_title": podcast.title if podcast else '',
        "podcast_url": podcast.url if podcast else '',
        "description": episode.description,
        "website": episode.link,
        "mygpo_link": 'http://%(domain)s%(res)s' % dict(domain=domain,
            res=get_episode_link_target(episode, podcast)) if podcast else ''
        }

    if episode.released:
        data['released'] = episode.released.strftime('%Y-%m-%dT%H:%M:%S')

    return data
