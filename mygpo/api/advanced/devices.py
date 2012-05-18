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

from functools import partial
from itertools import chain
from collections import namedtuple
from datetime import datetime

import gevent

from django.http import HttpResponse
from django.contrib.sites.models import RequestSite
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from mygpo.api.constants import DEVICE_TYPES
from mygpo.api.advanced import AdvancedAPIEndpoint
from mygpo.api.advanced.directory import episode_data, podcast_data
from mygpo.api.backend import get_device, get_subscription_change_urls, \
         clean_episode_action_data
from mygpo.utils import parse_bool, get_timestamp
from mygpo.core.models import Episode
from mygpo.api.basic_auth import require_valid_user, check_username





class DeviceEndpoint(AdvancedAPIEndpoint):

    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(never_cache)
    def post(self, request, username, device_uid):

        d = get_device(request.user, device_uid,
                request.META.get('HTTP_USER_AGENT', ''))

        data = self.get_post_data(request)

        if 'caption' in data:
            if not data['caption']:
                raise APIParameterException('caption must not be empty')
            d.name = data['caption']

        if 'type' in data:
            if not self.valid_devicetype(data['type']):
               raise APIParameterException('invalid device type %s' % data['type'])
            d.type = data['type']

        request.user.update_device(d)

        return HttpResponse()

    # Workaround for mygpoclient 1.0: It uses "PUT" requests
    # instead of "POST" requests for uploading device settings
    put = post


    def valid_devicetype(self, device_type):
        return device_type in [t[0] for t in DEVICE_TYPES]



class DeviceListEndpoint(AdvancedAPIEndpoint):

    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(never_cache)
    def get(self, request, username):
        devices = filter(lambda d: not d.deleted, request.user.devices)
        devices = map(self.device_data, devices)
        return devices


    def device_data(self, device):
        return dict(
            id           = device.uid,
            caption      = device.name,
            type         = device.type,
            subscriptions= len(device.get_subscribed_podcast_ids())
        )


EpisodeStatus = namedtuple('EpisodeStatus', 'episode status action')


class DeviceUpdateEndpoint(AdvancedAPIEndpoint):
    """ Returns Updates for a Device

    API Documentation:
    http://wiki.gpodder.org/wiki/Web_Services/API_2#Retrieve_Updates_for_a_Device
    """

    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(never_cache)
    def get(self, request, username, device_uid):
        now = datetime.now()
        since = self.get_since(request)

        device = request.user.get_device_by_uid(device_uid)

        include_actions = parse_bool(request.GET.get('include_actions', False))
        until_ = get_timestamp(now)
        domain = RequestSite(request).domain
        subscriptions = list(device.get_subscribed_podcasts())

        add_urls, remove_urls = get_subscription_change_urls(device, since, now)

        add_podcasts = self.get_added_podcasts(add_urls, subscriptions, domain)

        updates = self.get_updates(request.user, subscriptions, domain,
                include_actions, since)

        return {
            'add': add_podcasts,
            'remove': remove_urls,
            'updates': updates,
            'timestamp': until_,
        }


    def get_since(self, request):
        since_ = request.GET.get('since', None)

        if since_ == None:
            raise APIParameterException('parameter since missing')

        try:
            return datetime.fromtimestamp(float(since_))
        except ValueError:
            raise APIParameterException('since-value is not a valid timestamp')



    def get_updates(self, user, podcasts, domain, include_actions, since):

        # index data
        devices = dict( (dev.id, dev.uid) for dev in user.devices )
        id_podcasts = dict( (p.get_id(), p) for p in podcasts )

        prepare_episode_data = partial(self.get_episode_data, id_podcasts,
                domain, devices, include_actions)

        episode_updates = get_episode_updates(user, subscriptions, since)

        return map(prepare_episode_data, episode_updates)


    def get_episode_updates(user, subscribed_podcasts, since):
        """ Returns the episode updates since the timestamp """

        states = {}

        # get episodes
        episode_jobs = [gevent.spawn(p.get_episodes, since) for p in
            subscribed_podcasts]
        gevent.joinall(episode_jobs)
        episodes = chain.from_iterable(job.get() for job in episode_jobs)

        for episode in episodes:
            states[episode._id] = EpisodeStatus(episode, 'new', None)

        # get episode states
        e_action_jobs = [gevent.spawn(p.get_episode_states, user._id) for p in
            subscribed_podcasts]
        gevent.joinall(e_action_jobs)
        e_actions = chain.from_iterable(job.get() for job in e_action_jobs)

        for action in e_actions:
            e_id = action['episode_id']

            if e_id in states:
                episode = states[e_id].episode
            else:
                episode = Episode.get(e_id)

            states[e_id] = EpisodeStatus(episode, action['action'], action)

        return states.itervalues()


    def get_episode_data(self, podcasts, domain, devices, include_actions,
            episode_status):
        """ Get episode data for an episode status object """

        podcast_id = episode_status.episode.podcast
        podcast = podcasts.get(podcast_id, None)
        t = episode_data(episode_status.episode, domain, podcast)
        t['status'] = episode_status.status

        # include latest action (bug 1419)
        if include_actions and episode_status.action:
            t['action'] = clean_episode_action_data(episode_status.action, devices)

        return t



    def get_added_podcasts(self, add_urls, subscriptions, domain):
        podcasts = dict( (p.url, p) for p in subscriptions )
        prepare_podcast_data = partial(self.get_podcast_data, podcasts, domain)
        return map(prepare_podcast_data, add_urls)



    def get_podcast_data(self, podcasts, domain, url):
        """ Gets podcast data for a URL from a dict of podcasts """
        podcast = podcasts.get(url)
        return podcast_data(podcast, domain)
