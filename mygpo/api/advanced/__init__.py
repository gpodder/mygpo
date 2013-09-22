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
from collections import defaultdict, namedtuple
from datetime import datetime
from importlib import import_module

import dateutil.parser

from django.http import HttpResponse, HttpResponseBadRequest, Http404, HttpResponseNotFound
from django.contrib.sites.models import RequestSite
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.conf import settings as dsettings

from mygpo.api.constants import EPISODE_ACTION_TYPES, DEVICE_TYPES
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.advanced.directory import episode_data
from mygpo.api.backend import get_device, BulkSubscribe
from mygpo.utils import format_time, parse_bool, get_timestamp, \
    parse_request_body, normalize_feed_url
from mygpo.decorators import allowed_methods
from mygpo.core.tasks import auto_flattr_episode
from mygpo.users.models import EpisodeAction, \
     DeviceDoesNotExist, DeviceUIDException, \
     InvalidEpisodeActionAttributes
from mygpo.users.settings import FLATTR_AUTO
from mygpo.core.json import JSONDecodeError
from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.db.couchdb import BulkException, bulk_save_retry, \
    get_userdata_database
from mygpo.db.couchdb.episode import favorite_episodes_for_user
from mygpo.db.couchdb.podcast import podcast_for_url
from mygpo.db.couchdb.podcast_state import subscribed_podcast_ids_by_device
from mygpo.db.couchdb.episode_state import episode_state_for_ref_urls, \
    get_episode_actions
from mygpo.db.couchdb.user import set_device


import logging
logger = logging.getLogger(__name__)


# keys that are allowed in episode actions
EPISODE_ACTION_KEYS = ('position', 'episode', 'action', 'device', 'timestamp',
                       'started', 'total', 'podcast')


@csrf_exempt
@require_valid_user
@check_username
@never_cache
@allowed_methods(['GET', 'POST'])
def subscriptions(request, username, device_uid):

    now = datetime.now()
    now_ = get_timestamp(now)

    if request.method == 'GET':

        try:
            device = request.user.get_device_by_uid(device_uid)
        except DeviceDoesNotExist as e:
            return HttpResponseNotFound(str(e))

        since_ = request.GET.get('since', None)
        if since_ is None:
            return HttpResponseBadRequest('parameter since missing')
        try:
            since = datetime.fromtimestamp(float(since_))
        except ValueError:
            return HttpResponseBadRequest('since-value is not a valid timestamp')

        changes = get_subscription_changes(request.user, device, since, now)

        return JsonResponse(changes)

    elif request.method == 'POST':
        d = get_device(request.user, device_uid,
                request.META.get('HTTP_USER_AGENT', ''))

        if not request.body:
            return HttpResponseBadRequest('POST data must not be empty')

        try:
            actions = parse_request_body(request)
        except (JSONDecodeError, UnicodeDecodeError, ValueError) as e:
            msg = (u'Could not decode subscription update POST data for ' +
                   'user %s: %s') % (username,
                   request.body.decode('ascii', errors='replace'))
            logger.exception(msg)
            return HttpResponseBadRequest(msg)

        add = actions['add'] if 'add' in actions else []
        rem = actions['remove'] if 'remove' in actions else []

        add = filter(None, add)
        rem = filter(None, rem)

        try:
            update_urls = update_subscriptions(request.user, d, add, rem)
        except ValueError, e:
            return HttpResponseBadRequest(e)

        return JsonResponse({
            'timestamp': now_,
            'update_urls': update_urls,
            })


def update_subscriptions(user, device, add, remove):

    for a in add:
        if a in remove:
            raise ValueError('can not add and remove %s at the same time' % a)

    add_s = map(normalize_feed_url, add)
    rem_s = map(normalize_feed_url, remove)

    assert len(add) == len(add_s) and len(remove) == len(rem_s)

    updated_urls = filter(lambda (a, b): a != b, zip(add + remove, add_s + rem_s))

    add_s = filter(None, add_s)
    rem_s = filter(None, rem_s)

    # If two different URLs (in add and remove) have
    # been sanitized to the same, we ignore the removal
    rem_s = filter(lambda x: x not in add_s, rem_s)

    subscriber = BulkSubscribe(user, device)

    for a in add_s:
        subscriber.add_action(a, 'subscribe')

    for r in rem_s:
        subscriber.add_action(r, 'unsubscribe')

    try:
        subscriber.execute()
    except BulkException as be:
        for err in be.errors:
            loger.error('Advanced API: %(username)s: Updating subscription for '
                    '%(podcast_url)s on %(device_uid)s failed: '
                    '%(rerror)s (%(reason)s)'.format(username=user.username,
                        podcast_url=err.doc, device_uid=device.uid,
                        error=err.error, reason=err.reason)
                )

    return updated_urls


def get_subscription_changes(user, device, since, until):
    add_urls, rem_urls = device.get_subscription_changes(since, until)
    until_ = get_timestamp(until)
    return {'add': add_urls, 'remove': rem_urls, 'timestamp': until_}


@csrf_exempt
@require_valid_user
@check_username
@never_cache
@allowed_methods(['GET', 'POST'])
def episodes(request, username, version=1):

    version = int(version)
    now = datetime.now()
    now_ = get_timestamp(now)
    ua_string = request.META.get('HTTP_USER_AGENT', '')

    if request.method == 'POST':
        try:
            actions = parse_request_body(request)
        except (JSONDecodeError, UnicodeDecodeError, ValueError) as e:
            msg = ('Could not decode episode update POST data for ' +
                   'user %s: %s') % (username,
                   request.body.decode('ascii', errors='replace'))
            logger.exception(msg)
            return HttpResponseBadRequest(msg)

        logger.info('start: user %s: %d actions from %s' % (request.user._id, len(actions), ua_string))

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
        except DeviceUIDException as e:
            logger.warn('invalid device UID while uploading episode actions for user %s', username)
            return HttpResponseBadRequest(str(e))

        except InvalidEpisodeActionAttributes as e:
            logger.exception('invalid episode action attributes while uploading episode actions for user %s' % (username,))
            return HttpResponseBadRequest(str(e))

        logger.info('done:  user %s: %d actions from %s' % (request.user._id, len(actions), ua_string))
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
            podcast = podcast_for_url(podcast_url)
            if not podcast:
                raise Http404
        else:
            podcast = None

        if device_uid:

            try:
                device = request.user.get_device_by_uid(device_uid)
            except DeviceDoesNotExist as e:
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

    devices = dict( (dev.id, dev.uid) for dev in user.devices )

    args = {}
    if podcast is not None:
        args['podcast_id'] = podcast.get_id()

    if device is not None:
        args['device_id'] = device.id

    actions = get_episode_actions(user._id, since, until, **args)

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

    if user.get_wksetting(FLATTR_AUTO):
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
        new_action.device = device.id

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
def device(request, username, device_uid):
    d = get_device(request.user, device_uid,
            request.META.get('HTTP_USER_AGENT', ''))

    try:
        data = parse_request_body(request)
    except (JSONDecodeError, UnicodeDecodeError, ValueError) as e:
        msg = ('Could not decode device update POST data for ' +
               'user %s: %s') % (username,
               request.body.decode('ascii', errors='replace'))
        logger.exception(msg)
        return HttpResponseBadRequest(msg)

    if 'caption' in data:
        if not data['caption']:
            return HttpResponseBadRequest('caption must not be empty')
        d.name = data['caption']

    if 'type' in data:
        if not valid_devicetype(data['type']):
            return HttpResponseBadRequest('invalid device type %s' % data['type'])
        d.type = data['type']


    set_device(request.user, d)

    return HttpResponse()


def valid_devicetype(type):
    for t in DEVICE_TYPES:
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
def devices(request, username):
    devices = filter(lambda d: not d.deleted, request.user.devices)
    devices = map(device_data, devices)
    return JsonResponse(devices)


def device_data(device):
    return dict(
        id           = device.uid,
        caption      = device.name,
        type         = device.type,
        subscriptions= len(subscribed_podcast_ids_by_device(device)),
    )


@require_valid_user
@check_username
@never_cache
def favorites(request, username):
    favorites = favorite_episodes_for_user(request.user)
    domain = RequestSite(request).domain
    e_data = lambda e: episode_data(e, domain)
    ret = map(e_data, favorites)
    return JsonResponse(ret)


def sanitize_append(url, sanitized_list):
    urls = normalize_feed_url(url)
    if url != urls:
        sanitized_list.append( (url, urls or '') )
    return urls
