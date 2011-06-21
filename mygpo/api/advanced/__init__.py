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

from itertools import imap, chain
from collections import defaultdict, namedtuple
from mygpo.api.basic_auth import require_valid_user, check_username
from django.http import HttpResponse, HttpResponseBadRequest
from mygpo.api.models import Device, Podcast, Episode, EPISODE_ACTION_TYPES, DEVICE_TYPES
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.sanitizing import sanitize_url, sanitize_urls
from mygpo.api.advanced.directory import episode_data, podcast_data
from mygpo.api.backend import get_device, get_favorites
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import RequestSite
from time import strftime
from datetime import datetime
import dateutil.parser
from mygpo.log import log
from mygpo.utils import parse_time, parse_bool, get_to_dict, get_timestamp
from mygpo.decorators import allowed_methods
from mygpo.core import models
from mygpo.core.models import SanitizingRule
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from mygpo.users.models import PodcastUserState, EpisodeAction, EpisodeUserState
from mygpo import migrate

try:
    import simplejson as json
except ImportError:
    import json


# keys that are allowed in episode actions
EPISODE_ACTION_KEYS = ('position', 'episode', 'action', 'device', 'timestamp',
                       'started', 'total', 'podcast')


@csrf_exempt
@require_valid_user
@check_username
@allowed_methods(['GET', 'POST'])
def subscriptions(request, username, device_uid):

    now = datetime.now()
    now_ = get_timestamp(now)

    if request.method == 'GET':
        d = get_object_or_404(Device, user=request.user, uid=device_uid, deleted=False)

        since_ = request.GET.get('since', None)
        if since_ == None:
            return HttpResponseBadRequest('parameter since missing')
        try:
            since = datetime.fromtimestamp(float(since_))
        except ValueError:
            return HttpResponseBadRequest('since-value is not a valid timestamp')

        dev = migrate.get_or_migrate_device(d)
        changes = get_subscription_changes(request.user, dev, since, now)

        return JsonResponse(changes)

    elif request.method == 'POST':
        d = get_device(request.user, device_uid)

        actions = json.loads(request.raw_post_data)
        add = actions['add'] if 'add' in actions else []
        rem = actions['remove'] if 'remove' in actions else []

        add = filter(None, add)
        rem = filter(None, rem)

        try:
            update_urls = update_subscriptions(request.user, d, add, rem)
        except IntegrityError, e:
            return HttpResponseBadRequest(e)

        return JsonResponse({
            'timestamp': now_, 
            'update_urls': update_urls,
            })


def update_subscriptions(user, device, add, remove):

    for a in add:
        if a in remove:
            raise IntegrityError('can not add and remove %s at the same time' % a)

    add_s = list(sanitize_urls(add, 'podcast'))
    rem_s = list(sanitize_urls(remove, 'podcast'))

    assert len(add) == len(add_s) and len(remove) == len(rem_s)

    updated_urls = filter(lambda (a, b): a != b, zip(add + remove, add_s + rem_s))

    add_s = filter(None, add_s)
    rem_s = filter(None, rem_s)

    # If two different URLs (in add and remove) have
    # been sanitized to the same, we ignore the removal
    rem_s = filter(lambda x: x not in add_s, rem_s)

    for a in add_s:
        p, p_created = Podcast.objects.get_or_create(url=a)
        p = migrate.get_or_migrate_podcast(p)
        try:
            p.subscribe(device)
        except Exception as e:
            log('Advanced API: %(username)s: could not subscribe to podcast %(podcast_url)s on device %(device_id)s: %(exception)s' %
                {'username': user.username, 'podcast_url': p.url, 'device_id': device.id, 'exception': e})

    for r in rem_s:
        p, p_created = Podcast.objects.get_or_create(url=r)
        p = migrate.get_or_migrate_podcast(p)
        try:
            p.unsubscribe(device)
        except Exception as e:
            log('Advanced API: %(username)s: could not unsubscribe from podcast %(podcast_url)s on device %(device_id)s: %(exception)s' %
                {'username': user.username, 'podcast_url': p.url, 'device_id': device.id, 'exception': e})

    return updated_urls


def get_subscription_changes(user, device, since, until):
    add, rem = device.get_subscription_changes(since, until)

    podcast_ids = add + rem
    podcasts = get_to_dict(models.Podcast, podcast_ids, get_id=models.Podcast.get_id)

    add_podcasts = filter(None, (podcasts.get(i, None) for i in add))
    rem_podcasts = filter(None, (podcasts.get(i, None) for i in rem))
    add_urls = [ podcast.url for podcast in add_podcasts]
    rem_urls = [ podcast.url for podcast in rem_podcasts]

    until_ = get_timestamp(until)
    return {'add': add_urls, 'remove': rem_urls, 'timestamp': until_}


@csrf_exempt
@require_valid_user
@check_username
@allowed_methods(['GET', 'POST'])
def episodes(request, username, version=1):

    version = int(version)
    now = datetime.now()
    now_ = get_timestamp(now)

    if request.method == 'POST':
        try:
            actions = json.loads(request.raw_post_data)
        except KeyError, e:
            log('could not parse episode update info for user %s: %s' % (username, e))
            return HttpResponseBadRequest()

        try:
            update_urls = update_episodes(request.user, actions)
        except Exception, e:
            log('could not update episodes for user %s: %s' % (username, e))
            raise
            return HttpResponseBadRequest(e)

        return JsonResponse({'timestamp': now_, 'update_urls': update_urls})

    elif request.method == 'GET':
        podcast_url= request.GET.get('podcast', None)
        device_uid = request.GET.get('device', None)
        since_     = request.GET.get('since', None)
        aggregated = parse_bool(request.GET.get('aggregated', False))

        try:
            since = datetime.fromtimestamp(float(since_)) if since_ else None
        except ValueError:
            return HttpResponseBadRequest('since-value is not a valid timestamp')

        podcast = get_object_or_404(Podcast, url=podcast_url) if podcast_url else None
        device  = get_object_or_404(Device, user=request.user,uid=device_uid, deleted=False) if device_uid else None

        return JsonResponse(get_episode_changes(request.user, podcast, device, since, now, aggregated, version))


def get_episode_changes(user, podcast, device, since, until, aggregated, version):

    new_user = migrate.get_or_migrate_user(user)
    devices = dict( (dev.oldid, dev.uid) for dev in new_user.devices )

    args = {}
    if podcast is not None: args['podcast_id'] = podcast.get_id()
    if device is not None:  args['device_oldid'] = device.id

    actions = EpisodeAction.filter(user.id, since, until, *args)

    if aggregated:
        actions = dict( (a['podcast'], a) for a in actions ).values()

    if version == 1:
        # convert position parameter for API 1 compatibility
        def convert_position(action):
            pos = action.get('position', None)
            if pos is not None:
                action['position'] = strftime('%H:%M:%S', pos)
            return action

        actions = imap(convert_position, actions)


    def clean_data(action):
        action['podcast'] = action['podcast_url']
        action['episode'] = action['episode_url']

        if 'device_oldid' in action:
            action['device'] = devices[action['device_oldid']]
            del action['device_oldid']

        # remove superfluous keys
        for x in action.keys():
            if x not in EPISODE_ACTION_KEYS:
                del action[x]

        # set missing keys to None
        for x in EPISODE_ACTION_KEYS:
            if x not in action:
                action[x] = None

        return action

    actions = map(clean_data, actions)

    until_ = get_timestamp(until)

    return {'actions': actions, 'timestamp': until_}


def update_episodes(user, actions):
    update_urls = []

    grouped_actions = defaultdict(list)

    # group all actions by their episode
    for action in actions:
        podcast_url = action['podcast']
        podcast_url = sanitize_append(podcast_url, 'podcast', update_urls)
        if podcast_url == '': continue

        episode_url = action['episode']
        episode_url = sanitize_append(episode_url, 'episode', update_urls)
        if episode_url == '': continue

        new_user = migrate.get_or_migrate_user(user)
        act = parse_episode_action(action, new_user, update_urls)
        grouped_actions[ (podcast_url, episode_url) ].append(act)

    # load the episode state only once for every episode
    for (p_url, e_url), action_list in grouped_actions.iteritems():
        episode_state = EpisodeUserState.for_ref_urls(user, p_url, e_url)
        episode_state.add_actions(action_list)
        episode_state.save()

    return update_urls


def parse_episode_action(action, user, update_urls):
    action_str  = action.get('action', None)
    if not valid_episodeaction(action_str):
        raise Exception('invalid action %s' % action_str)

    new_action = EpisodeAction()

    new_action.action = action['action']

    if action.get('device', False):
        device = user.get_device_by_uid(action['device'])
        new_action.device_oldid = device.oldid
        new_action.device = device.id

    if action.get('timestamp', False):
        new_action.timestamp = dateutil.parser.parse(action['timestamp'])

    new_action.started = action.get('started', None)
    new_action.playmark = action.get('position', None)
    new_action.total = action.get('total', None)

    return new_action


@csrf_exempt
@require_valid_user
@check_username
# Workaround for mygpoclient 1.0: It uses "PUT" requests
# instead of "POST" requests for uploading device settings
@allowed_methods(['POST', 'PUT'])
def device(request, username, device_uid):
    d = get_device(request.user, device_uid)

    data = json.loads(request.raw_post_data)

    if 'caption' in data:
        d.name = data['caption']

    if 'type' in data:
        if not valid_devicetype(data['type']):
           return HttpResponseBadRequest('invalid device type %s' % data['type'])
        d.type = data['type']

    d.save()

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
@allowed_methods(['GET'])
def devices(request, username):
    devices = Device.objects.filter(user=request.user, deleted=False)
    devices = map(migrate.get_or_migrate_device, devices)
    devices = map(device_data, devices)

    return JsonResponse(devices)


def device_data(device):
    return dict(
        id           = device.uid,
        caption      = device.name,
        type         = device.type,
        subscriptions= len(device.get_subscribed_podcast_ids())
    )


@csrf_exempt
@require_valid_user
@check_username
def updates(request, username, device_uid):
    now = datetime.now()
    now_ = get_timestamp(now)

    device = get_object_or_404(Device, user=request.user, uid=device_uid)

    since_ = request.GET.get('since', None)
    if since_ == None:
        return HttpResponseBadRequest('parameter since missing')
    try:
        since = datetime.fromtimestamp(float(since_))
    except ValueError:
        return HttpResponseBadRequest('since-value is not a valid timestamp')

    dev = migrate.get_or_migrate_device(device)
    ret = get_subscription_changes(request.user, dev, since, now)
    domain = RequestSite(request).domain

    subscriptions = dev.get_subscribed_podcasts()

    podcasts = dict( (p.url, p) for p in subscriptions )

    def prepare_podcast_data(url):
        podcast = podcasts.get(url)
        return podcast_data(podcast, domain)

    ret['add'] = map(prepare_podcast_data, ret['add'])


    # index subscribed podcasts by their Id for fast access
    podcasts = dict( (p.get_id(), p) for p in subscriptions )

    def prepare_episode_data(episode_status):
        """ converts the data to primitives that converted to JSON """
        podcast_id = episode_status.episode.podcast
        podcast = podcasts.get(podcast_id, None)
        t = episode_data(episode_status.episode, domain, podcast)
        t['status'] = episode_status.status
        return t

    episode_updates = get_episode_updates(request.user, subscriptions, since)
    ret['updates'] = map(prepare_episode_data, episode_updates)

    return JsonResponse(ret)


def get_episode_updates(user, subscribed_podcasts, since):
    """ Returns the episode updates since the timestamp """

    EpisodeStatus = namedtuple('EpisodeStatus', 'episode status')

    subscriptions_oldpodcasts = [p.get_old_obj() for p in subscribed_podcasts]

    episode_status = {}
    #TODO: changes this to a get_multi when episodes have been migrated
    for e in Episode.objects.filter(podcast__in=subscriptions_oldpodcasts, timestamp__gte=since).order_by('timestamp'):
        episode = migrate.get_or_migrate_episode(e)
        episode_status[episode._id] = EpisodeStatus(episode, 'new')

    e_actions = (p.get_episode_states(user.id) for p in subscribed_podcasts)
    e_actions = chain.from_iterable(e_actions)

    for action in e_actions:
        e_id = action['episode_id']

        if e_id in episode_status:
            episode = episode_status[e_id].episode
        else:
            episode = models.Episode.get(e_id)

        episode_status[e_id] = EpisodeStatus(episode, action['action'])

    return episode_status.itervalues()


@require_valid_user
@check_username
def favorites(request, username):
    favorites = get_favorites(request.user)
    domain = RequestSite(request).domain
    e_data = lambda e: episode_data(e, domain)
    ret = map(e_data, favorites)
    return JsonResponse(ret)


def sanitize_append(url, obj_type, sanitized_list):
    urls = sanitize_url(url, obj_type)
    if url != urls:
        sanitized_list.append( (url, urls) )
    return urls
