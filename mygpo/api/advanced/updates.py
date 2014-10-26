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

from itertools import chain
from datetime import datetime

from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.contrib.sites.models import RequestSite
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views.generic.base import View

from mygpo.podcasts.models import Episode
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.advanced import episode_action_json
from mygpo.api.advanced.directory import episode_data, podcast_data
from mygpo.utils import parse_bool, get_timestamp
from mygpo.subscriptions import get_subscription_history, subscription_diff
from mygpo.users.models import Client
from mygpo.episodestates.models import EpisodeState
from mygpo.users.subscriptions import subscription_changes, podcasts_for_states
from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.decorators import cors_origin

from collections import namedtuple
EpisodeStatus = namedtuple('EpisodeStatus', 'episode status action')

import logging
logger = logging.getLogger(__name__)


class DeviceUpdates(View):
    """ returns various updates for a device

    http://wiki.gpodder.org/wiki/Web_Services/API_2/Devices#Get_Updates """

    @method_decorator(csrf_exempt)
    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(never_cache)
    @method_decorator(cors_origin())
    def get(self, request, username, device_uid):

        now = datetime.utcnow()
        now_ = get_timestamp(now)

        user = request.user

        try:
            device = user.client_set.get(uid=device_uid)
        except Client.DoesNotExist as e:
            return HttpResponseNotFound(str(e))

        try:
            since = self.get_since(request)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

        include_actions = parse_bool(request.GET.get('include_actions', False))

        domain = RequestSite(request).domain

        add, rem, subscriptions = self.get_subscription_changes(user, device,
                                                                since, now,
                                                                domain)
        updates = self.get_episode_changes(user, subscriptions, domain,
                                           include_actions, since)

        return JsonResponse({
            'add': add,
            'rem': rem,
            'updates': updates,
            'timestamp': get_timestamp(now),
        })


    def get_subscription_changes(self, user, device, since, now, domain):
        """ gets new, removed and current subscriptions """

        history = get_subscription_history(user, device, since, now)
        add, rem = subscription_diff(history)

        subscriptions = device.get_subscribed_podcasts()

        add = [podcast_data(p, domain) for p in add]
        rem = [p.url for p in rem]

        return add, rem, subscriptions


    def get_episode_changes(self, user, subscriptions, domain, include_actions, since):
        devices = {dev.id.hex: dev.uid for dev in user.client_set.all()}

        # index subscribed podcasts by their Id for fast access
        podcasts = {p.get_id(): p for p in subscriptions}

        episode_updates = self.get_episode_updates(user, subscriptions, since)

        return [self.get_episode_data(status, podcasts, domain,
                include_actions, user, devices) for status in episode_updates]


    def get_episode_updates(self, user, subscribed_podcasts, since,
            max_per_podcast=5):
        """ Returns the episode updates since the timestamp """

        episodes = []
        for podcast in subscribed_podcasts:
            episodes.extend(Episode.objects.filter(
                                podcast=podcast,
                                released__gt=since
                                ).order_by('-released')[:max_per_podcast]
            )

        states = EpisodeState.dict_for_user(user, episodes)

        for episode in episodes:
            yield EpisodeStatus(episode, states.get(episode.id, 'new'), None)


    def get_episode_data(self, episode_status, podcasts, domain, include_actions, user, devices):
        """ Get episode data for an episode status object """

        # TODO: shouldn't the podcast_id be in the episode status?
        podcast_id = episode_status.episode.podcast
        podcast = podcasts.get(podcast_id, None)
        t = episode_data(episode_status.episode, domain, podcast)
        t['status'] = episode_status.status

        # include latest action (bug 1419)
        # TODO
        if include_actions and episode_status.action:
            t['action'] = episode_action_json(episode_status.action, user)

        return t

    def get_since(self, request):
        """ parses the "since" parameter """
        since_ = request.GET.get('since', None)
        if since_ is None:
            raise ValueError('parameter since missing')
        try:
            return datetime.fromtimestamp(float(since_))
        except ValueError as e:
            raise ValueError("'since' is not a valid timestamp: %s" % str(e))
