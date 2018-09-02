from functools import partial

from collections import defaultdict
from datetime import datetime
from importlib import import_module

import dateutil.parser

from django.http import (HttpResponse, HttpResponseBadRequest, Http404,
                         HttpResponseNotFound, )
from django.core.exceptions import ValidationError
from django.contrib.sites.requests import RequestSite
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
from mygpo.history.models import EpisodeHistoryEntry
from mygpo.users.models import Client, InvalidEpisodeActionAttributes
from mygpo.favorites.models import FavoriteEpisode
from mygpo.api.basic_auth import require_valid_user, check_username


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
@cors_origin()
def episodes(request, username, version=1):

    version = int(version)
    now = datetime.utcnow()
    now_ = get_timestamp(now)
    ua_string = request.META.get('HTTP_USER_AGENT', '')

    if request.method == 'POST':
        try:
            actions = parse_request_body(request)
        except (UnicodeDecodeError, ValueError) as e:
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
            logger.warning('Validation Error while uploading episode actions '
                'for user %s: %s', username, str(e))
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
            if since is not None:
                since = datetime.utcfromtimestamp(since)
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
                now, aggregated, version)

        return JsonResponse(changes)



def convert_position(action):
    """ convert position parameter for API 1 compatibility """
    pos = getattr(action, 'position', None)
    if pos is not None:
        action.position = format_time(pos)
    return action



def get_episode_changes(user, podcast, device, since, until, aggregated, version):

    history = EpisodeHistoryEntry.objects.filter(user=user,
                                                 timestamp__lt=until)

    # return the earlier entries first
    history = history.order_by('timestamp')

    if since:
        history = history.filter(timestamp__gte=since)

    if podcast is not None:
        history = history.filter(episode__podcast=podcast)

    if device is not None:
        history = history.filter(client=device)

    if version == 1:
        history = map(convert_position, history)

    # Limit number of returned episode actions
    max_actions = dsettings.MAX_EPISODE_ACTIONS
    history = history[:max_actions]

    # evaluate query and turn into list, for negative indexing
    history = list(history)

    actions = [episode_action_json(a, user) for a in history]

    if aggregated:
        actions = list(dict( (a['episode'], a) for a in actions ).values())

    if history:
        ts = get_timestamp(history[-1].timestamp)
    else:
        ts = get_timestamp(until)

    return {'actions': actions, 'timestamp': ts}


def episode_action_json(history, user):

    action = {
        'podcast': history.podcast_ref_url or history.episode.podcast.url,
        'episode': history.episode_ref_url or history.episode.url,
        'action': history.action,
        'timestamp': history.timestamp.isoformat(),
    }

    if history.client:
        action['device'] = history.client.uid

    if history.action == EpisodeHistoryEntry.PLAY:
        action['started'] = history.started
        action['position'] = history.stopped  # TODO: check "playmark"
        action['total'] = history.total

    return action


def update_episodes(user, actions, now, ua_string):
    update_urls = []

    # group all actions by their episode
    for action in actions:

        podcast_url = action.get('podcast', '')
        podcast_url = sanitize_append(podcast_url, update_urls)
        if not podcast_url:
            continue

        episode_url = action.get('episode', '')
        episode_url = sanitize_append(episode_url, update_urls)
        if not episode_url:
            continue

        podcast = Podcast.objects.get_or_create_for_url(podcast_url).object
        episode = Episode.objects.get_or_create_for_url(podcast, episode_url).object

        # parse_episode_action returns a EpisodeHistoryEntry obj
        history = parse_episode_action(action, user, update_urls, now,
                                       ua_string)

        EpisodeHistoryEntry.create_entry(user, episode, history.action,
                                         history.client, history.timestamp,
                                         history.started, history.stopped,
                                         history.total, podcast_url,
                                         episode_url)

    return update_urls


def parse_episode_action(action, user, update_urls, now, ua_string):
    action_str  = action.get('action', None)
    if not valid_episodeaction(action_str):
        raise Exception('invalid action %s' % action_str)

    history = EpisodeHistoryEntry()

    history.action = action['action']

    if action.get('device', False):
        client = get_device(user, action['device'], ua_string)
        history.client = client

    if action.get('timestamp', False):
        history.timestamp = dateutil.parser.parse(action['timestamp'])
    else:
        history.timestamp = now

    history.started = action.get('started', None)
    history.stopped = action.get('position', None)
    history.total = action.get('total', None)

    return history


@csrf_exempt
@require_valid_user
@check_username
@never_cache
# Workaround for mygpoclient 1.0: It uses "PUT" requests
# instead of "POST" requests for uploading device settings
@allowed_methods(['POST', 'PUT'])
@cors_origin()
def device(request, username, device_uid, version=None):
    d = get_device(request.user, device_uid,
            request.META.get('HTTP_USER_AGENT', ''))

    try:
        data = parse_request_body(request)
    except (UnicodeDecodeError, ValueError) as e:
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
def devices(request, username, version=None):
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
    ret = list(map(e_data, favorites))
    return JsonResponse(ret)


def sanitize_append(url, sanitized_list):
    urls = normalize_feed_url(url)
    if url != urls:
        sanitized_list.append( (url, urls or '') )
    return urls
