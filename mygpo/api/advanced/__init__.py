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
from itertools import imap
from collections import defaultdict
from datetime import datetime
from importlib import import_module

import dateutil.parser

from django.http import (HttpResponse, HttpResponseBadRequest, Http404,
                         HttpResponseNotFound, )
from django.core.exceptions import ValidationError
from django.contrib.sites.models import RequestSite
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.conf import settings as dsettings
from django.shortcuts import get_object_or_404

from mygpo.podcasts.models import Podcast, Episode
from mygpo.subscriptions.models import Subscription
from mygpo.api.constants import EPISODE_ACTION_TYPES
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.advanced.directory import episode_data
from mygpo.api.backend import get_device
from mygpo.utils import format_time, parse_bool, get_timestamp, \
    parse_request_body, normalize_feed_url
from mygpo.decorators import allowed_methods, cors_origin
from mygpo.core.tasks import auto_flattr_episode
from mygpo.users.models import (EpisodeAction, Client,
                                InvalidEpisodeActionAttributes, )
from mygpo.users.settings import FLATTR_AUTO
from mygpo.favorites.models import FavoriteEpisode
from mygpo.core.json import JSONDecodeError
from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.db.couchdb import bulk_save_retry, get_userdata_database
from mygpo.db.couchdb.episode_state import episode_state_for_ref_urls, \
    get_episode_actions


import logging
logger = logging.getLogger(__name__)


class RequestException(Exception):
    """ Raised if the request is malfored or otherwise invalid """


# keys that are allowed in episode actions
EPISODE_ACTION_KEYS = ('position', 'episode', 'action', 'device', 'timestamp',
                       'started', 'total', 'podcast')


@csrf_exempt
@require_valid_user
@check_username
@never_cache
@allowed_methods(['GET', 'POST'])
@cors_origin()
def episodes(request, username, version=1):

    version = int(version)
    now = datetime.utcnow()
    now_ = get_timestamp(now)
    ua_string = request.META.get('HTTP_USER_AGENT', '')

    if request.method == 'POST':
        try:
            actions = parse_request_body(request)
        except (JSONDecodeError, UnicodeDecodeError, ValueError) as e:
            msg = ('Could not decode episode update POST data for ' +
                   'user %s: %s') % (username,
                   request.body.decode('ascii', errors='replace'))
            logger.warn(msg, exc_info=True)
            return HttpResponseBadRequest(msg)

        logger.info('start: user %s: %d actions from %s' % (request.user, len(actions), ua_string))

        # handle in background
        if len(actions) > dsettings.API_ACTIONS_MAX_NONBG:
            bg_handler = dsettings.API_ACTIONS_BG_HANDLER
            if bg_handler is not None:

                modname, funname = bg_handler.rsplit('.', 1)
                mod = import_module(modname)
                fun = getattr(mod, funname)

                fun(request.user, actions, now, ua_string)

                # TODO: return 202 Accepted
                return JsonResponse({'timestamp': now_, 'update_urls': []})


        try:
            update_urls = update_episodes(request.user, actions, now, ua_string)
        except ValidationError as e:
            logger.warn(u'Validation Error while uploading episode actions for user %s: %s', username, unicode(e))
            return HttpResponseBadRequest(str(e))

        except InvalidEpisodeActionAttributes as e:
            msg = 'invalid episode action attributes while uploading episode actions for user %s' % (username,)
            logger.warn(msg, exc_info=True)
            return HttpResponseBadRequest(str(e))

        logger.info('done:  user %s: %d actions from %s' % (request.user, len(actions), ua_string))
        return JsonResponse({'timestamp': now_, 'update_urls': update_urls})

    elif request.method == 'GET':
        podcast_url= request.GET.get('podcast', None)
        device_uid = request.GET.get('device', None)
        since_     = request.GET.get('since', None)
        aggregated = parse_bool(request.GET.get('aggregated', False))

        try:
            since = int(since_) if since_ else None
        except ValueError:
            return HttpResponseBadRequest('since-value is not a valid timestamp')

        if podcast_url:
            podcast = get_object_or_404(Podcast, urls__url=podcast_url)
        else:
            podcast = None

        if device_uid:

            try:
                user = request.user
                device = user.client_set.get(uid=device_uid)
            except Client.DoesNotExist as e:
                return HttpResponseNotFound(str(e))

        else:
            device = None

        changes = get_episode_changes(request.user, podcast, device, since,
                now_, aggregated, version)

        return JsonResponse(changes)



def convert_position(action):
    """ convert position parameter for API 1 compatibility """
    pos = getattr(action, 'position', None)
    if pos is not None:
        action.position = format_time(pos)
    return action



def get_episode_changes(user, podcast, device, since, until, aggregated, version):

    devices = {client.id.hex: client.uid for client in user.client_set.all()}

    args = {}
    if podcast is not None:
        args['podcast_id'] = podcast.get_id()

    if device is not None:
        args['device_id'] = device.id.hex

    actions, until = get_episode_actions(user.profile.uuid.hex, since, until, **args)

    if version == 1:
        actions = imap(convert_position, actions)

    clean_data = partial(clean_episode_action_data,
            user=user, devices=devices)

    actions = map(clean_data, actions)
    actions = filter(None, actions)

    if aggregated:
        actions = dict( (a['episode'], a) for a in actions ).values()

    return {'actions': actions, 'timestamp': until}




def clean_episode_action_data(action, user, devices):

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

    if action['action'] != 'play':
        if 'position' in action:
            del action['position']

        if 'total' in action:
            del action['total']

        if 'started' in action:
            del action['started']

        if 'playmark' in action:
            del action['playmark']

    else:
        action['position'] = action.get('position', False) or 0

    return action





def update_episodes(user, actions, now, ua_string):
    update_urls = []

    grouped_actions = defaultdict(list)

    # group all actions by their episode
    for action in actions:

        podcast_url = action['podcast']
        podcast_url = sanitize_append(podcast_url, update_urls)
        if podcast_url == '':
            continue

        episode_url = action['episode']
        episode_url = sanitize_append(episode_url, update_urls)
        if episode_url == '':
            continue

        act = parse_episode_action(action, user, update_urls, now, ua_string)
        grouped_actions[ (podcast_url, episode_url) ].append(act)


    auto_flattr_episodes = []

    # Prepare the updates for each episode state
    obj_funs = []

    for (p_url, e_url), action_list in grouped_actions.iteritems():
        episode_state = episode_state_for_ref_urls(user, p_url, e_url)

        if any(a['action'] == 'play' for a in actions):
            auto_flattr_episodes.append(episode_state.episode)

        fun = partial(update_episode_actions, action_list=action_list)
        obj_funs.append( (episode_state, fun) )

    udb = get_userdata_database()
    bulk_save_retry(obj_funs, udb)

    if user.profile.get_wksetting(FLATTR_AUTO):
        for episode_id in auto_flattr_episodes:
            auto_flattr_episode.delay(user, episode_id)

    return update_urls


def update_episode_actions(episode_state, action_list):
    """ Adds actions to the episode state and saves if necessary """

    len1 = len(episode_state.actions)
    episode_state.add_actions(action_list)

    if len(episode_state.actions) == len1:
        return None

    return episode_state



def parse_episode_action(action, user, update_urls, now, ua_string):
    action_str  = action.get('action', None)
    if not valid_episodeaction(action_str):
        raise Exception('invalid action %s' % action_str)

    new_action = EpisodeAction()

    new_action.action = action['action']

    if action.get('device', False):
        device = get_device(user, action['device'], ua_string)
        new_action.device = device.id.hex

    if action.get('timestamp', False):
        new_action.timestamp = dateutil.parser.parse(action['timestamp'])
    else:
        new_action.timestamp = now
    new_action.timestamp = new_action.timestamp.replace(microsecond=0)

    new_action.upload_timestamp = get_timestamp(now)

    new_action.started = action.get('started', None)
    new_action.playmark = action.get('position', None)
    new_action.total = action.get('total', None)

    return new_action


@csrf_exempt
@require_valid_user
@check_username
@never_cache
# Workaround for mygpoclient 1.0: It uses "PUT" requests
# instead of "POST" requests for uploading device settings
@allowed_methods(['POST', 'PUT'])
@cors_origin()
def device(request, username, device_uid):
    d = get_device(request.user, device_uid,
            request.META.get('HTTP_USER_AGENT', ''))

    try:
        data = parse_request_body(request)
    except (JSONDecodeError, UnicodeDecodeError, ValueError) as e:
        msg = ('Could not decode device update POST data for ' +
               'user %s: %s') % (username,
               request.body.decode('ascii', errors='replace'))
        logger.warn(msg, exc_info=True)
        return HttpResponseBadRequest(msg)

    if 'caption' in data:
        if not data['caption']:
            return HttpResponseBadRequest('caption must not be empty')
        d.name = data['caption']

    if 'type' in data:
        if not valid_devicetype(data['type']):
            return HttpResponseBadRequest('invalid device type %s' % data['type'])
        d.type = data['type']

    d.save()
    return HttpResponse()


def valid_devicetype(type):
    for t in Client.TYPES:
        if t[0] == type:
            return True
    return False

def valid_episodeaction(type):
    for t in EPISODE_ACTION_TYPES:
        if t[0] == type:
            return True
    return False


@csrf_exempt
@require_valid_user
@check_username
@never_cache
@allowed_methods(['GET'])
@cors_origin()
def devices(request, username):
    user = request.user
    clients = user.client_set.filter(deleted=False)
    client_data = [get_client_data(user, client) for client in clients]
    return JsonResponse(client_data)


def get_client_data(user, client):
    return dict(
        id           = client.uid,
        caption      = client.name,
        type         = client.type,
        subscriptions= Subscription.objects.filter(user=user, client=client)\
                                           .count(),
    )


@require_valid_user
@check_username
@never_cache
@cors_origin()
def favorites(request, username):
    favorites = FavoriteEpisode.episodes_for_user(request.user)
    domain = RequestSite(request).domain
    e_data = lambda e: episode_data(e, domain)
    ret = map(e_data, favorites)
    return JsonResponse(ret)


def sanitize_append(url, sanitized_list):
    urls = normalize_feed_url(url)
    if url != urls:
        sanitized_list.append( (url, urls or '') )
    return urls
