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
from itertools import imap, chain
from collections import defaultdict, namedtuple
from mygpo.api.basic_auth import require_valid_user, check_username
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from mygpo.api.models import EPISODE_ACTION_TYPES, DEVICE_TYPES
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.sanitizing import sanitize_url, sanitize_urls
from mygpo.api.advanced.directory import episode_data, podcast_data
from mygpo.api.backend import get_device, get_favorites
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import RequestSite
from datetime import datetime
import dateutil.parser
from mygpo.log import log
from mygpo.utils import parse_time, format_time, parse_bool, get_to_dict, get_timestamp
from mygpo.decorators import allowed_methods, repeat_on_conflict
from mygpo.core import models
from mygpo.core.models import SanitizingRule, Podcast
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from mygpo.users.models import PodcastUserState, EpisodeAction, EpisodeUserState
from mygpo import migrate

try:
    import simplejson as json
    JSONDecodeError = json.JSONDecodeError

except ImportError:
    import json
    JSONDecodeError = ValueError


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

    user = migrate.get_or_migrate_user(request.user)

    if request.method == 'GET':
        device = user.get_device_by_uid(device_uid)
        if not device or device.deleted:
            raise Http404

        since_ = request.GET.get('since', None)
        if since_ == None:
            return HttpResponseBadRequest('parameter since missing')
        try:
            since = datetime.fromtimestamp(float(since_))
        except ValueError:
            return HttpResponseBadRequest('since-value is not a valid timestamp')

        changes = get_subscription_changes(request.user, device, since, now)

        return JsonResponse(changes)

    elif request.method == 'POST':
        d = get_device(user, device_uid)

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
        p = Podcast.for_url(a, create=True)
        try:
            p.subscribe(user, device)
        except Exception as e:
            log('Advanced API: %(username)s: could not subscribe to podcast %(podcast_url)s on device %(device_id)s: %(exception)s' %
                {'username': user.username, 'podcast_url': p.url, 'device_id': device.id, 'exception': e})

    for r in rem_s:
        p = Podcast.for_url(r, create=True)
        try:
            p.unsubscribe(user, device)
        except Exception as e:
            log('Advanced API: %(username)s: could not unsubscribe from podcast %(podcast_url)s on device %(device_id)s: %(exception)s' %
                {'username': user.username, 'podcast_url': p.url, 'device_id': device.id, 'exception': e})

    return updated_urls


def get_subscription_changes(user, device, since, until):
    add, rem = device.get_subscription_changes(since, until)

    podcast_ids = add + rem
    podcasts = get_to_dict(Podcast, podcast_ids, get_id=models.Podcast.get_id)

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
        except (JSONDecodeError, UnicodeDecodeError) as e:
            log('Advanced API: could not decode episode update POST data for user %s: %s' % (username, e))
            return HttpResponseBadRequest()

        try:
            update_urls = update_episodes(request.user, actions, now)
        except Exception, e:
            import traceback
            log('could not update episodes for user %s: %s %s: %s' % (username, e, traceback.format_exc(), actions))
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

        if podcast_url:
            podcast = Podcast.for_url(podcast_url)
            if not podcast:
                raise Http404
        else:
            podcast = None

        if device_uid:
            user = migrate.get_or_migrate_user(request.user)
            device = user.get_device_by_uid(device_uid)

            if not device or device.deleted:
                raise Http404
        else:
            device = None

        return JsonResponse(get_episode_changes(request.user, podcast, device, since, now, aggregated, version))


def get_episode_changes(user, podcast, device, since, until, aggregated, version):

    new_user = migrate.get_or_migrate_user(user)
    devices = dict( (dev.id, dev.uid) for dev in new_user.devices )

    args = {}
    if podcast is not None: args['podcast_id'] = podcast.get_id()
    if device is not None:  args['device_id'] = device.id

    actions = EpisodeAction.filter(user.id, since, until, **args)

    if version == 1:
        # convert position parameter for API 1 compatibility
        def convert_position(action):
            pos = action.get('position', None)
            if pos is not None:
                action['position'] = format_time(pos)
            return action

        actions = imap(convert_position, actions)

    clean_data = partial(clean_episode_action_data,
            user=new_user, devices=devices)

    actions = map(clean_data, actions)
    actions = filter(None, actions)

    if aggregated:
        actions = dict( (a['episode'], a) for a in actions ).values()

    until_ = get_timestamp(until)

    return {'actions': actions, 'timestamp': until_}




def clean_episode_action_data(action, user, devices):
    action['podcast'] = action.get('podcast_url', None)
    action['episode'] = action.get('episode_url', None)

    if None in (action['podcast'], action['episode']):
        return None

    if 'device_id' in action:
        device_id = action['device_id']
        device = user.get_device(device_id)
        if device:
            action['device'] = device.uid

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






def update_episodes(user, actions, now):
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
        act = parse_episode_action(action, new_user, update_urls, now)
        grouped_actions[ (podcast_url, episode_url) ].append(act)

    # load the episode state only once for every episode
    for (p_url, e_url), action_list in grouped_actions.iteritems():
        episode_state = EpisodeUserState.for_ref_urls(user, p_url, e_url)

        if isinstance(episode_state, dict):
            from mygpo.log import log
            log('episode_state (%s, %s, %s): %s' % (user,
                        p_url, e_url, episode_state))


        @repeat_on_conflict(['episode_state'])
        def _update(episode_state):
            changed = False

            len1 = len(episode_state.actions)
            episode_state.add_actions(action_list)
            len2 = len(episode_state.actions)

            if len1 < len2:
                changed = True

            if episode_state.ref_url != e_url:
                episode_state.ref_url = e_url
                changed = True

            if episode_state.podcast_ref_url != p_url:
                episode_state.podcast_ref_url = p_url
                changed = True

            if changed:
                episode_state.save()


        _update(episode_state=episode_state)

    return update_urls


def parse_episode_action(action, user, update_urls, now):
    action_str  = action.get('action', None)
    if not valid_episodeaction(action_str):
        raise Exception('invalid action %s' % action_str)

    new_action = EpisodeAction()

    new_action.action = action['action']

    if action.get('device', False):
        device = get_device(user, action['device'])
        new_action.device = device.id

    if action.get('timestamp', False):
        new_action.timestamp = dateutil.parser.parse(action['timestamp'])
    else:
        new_action.timestamp = now
    new_action.timestamp = new_action.timestamp.replace(microsecond=0)

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
    user = migrate.get_or_migrate_user(request.user)
    d = get_device(user, device_uid)

    data = json.loads(request.raw_post_data)

    if 'caption' in data:
        if not data['caption']:
            raise HttpResponseBadRequest('caption must not be empty')
        d.name = data['caption']

    if 'type' in data:
        if not valid_devicetype(data['type']):
           return HttpResponseBadRequest('invalid device type %s' % data['type'])
        d.type = data['type']


    @repeat_on_conflict(['user'])
    def _update(user, device):
        user.set_device(device)
        user.save()

    _update(user=user, device=d)

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
    user = migrate.get_or_migrate_user(request.user)
    devices = filter(lambda d: not d.deleted, user.devices)
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

    user = migrate.get_or_migrate_user(request.user)
    device = user.get_device_by_uid(device_uid)
    if not device or device.deleted:
        raise Http404

    since_ = request.GET.get('since', None)
    if since_ == None:
        return HttpResponseBadRequest('parameter since missing')
    try:
        since = datetime.fromtimestamp(float(since_))
    except ValueError:
        return HttpResponseBadRequest('since-value is not a valid timestamp')

    include_actions = parse_bool(request.GET.get('include_actions', False))

    ret = get_subscription_changes(request.user, device, since, now)
    domain = RequestSite(request).domain

    subscriptions = list(device.get_subscribed_podcasts())

    podcasts = dict( (p.url, p) for p in subscriptions )

    def prepare_podcast_data(url):
        podcast = podcasts.get(url)
        try:
            return podcast_data(podcast, domain)
        except ValueError:
            from mygpo.log import log
            log('updates: podcast is None for url %s and dict %s' %
                    (url, podcasts.keys()))
            for k,v in podcasts.items():
                log('%s - %s' % (k, v))

            raise

    ret['add'] = map(prepare_podcast_data, ret['add'])

    devices = dict( (dev.id, dev.uid) for dev in user.devices )
    clean_data = partial(clean_episode_action_data,
            user=user, devices=devices)



    # index subscribed podcasts by their Id for fast access
    podcasts = dict( (p.get_id(), p) for p in subscriptions )

    def prepare_episode_data(episode_status):
        """ converts the data to primitives that converted to JSON """
        podcast_id = episode_status.episode.podcast
        podcast = podcasts.get(podcast_id, None)
        t = episode_data(episode_status.episode, domain, podcast)
        t['status'] = episode_status.status

        # include latest action (bug 1419)
        if include_actions and episode_status.action:
            t['action'] = clean_data(episode_status.action)

        return t

    episode_updates = get_episode_updates(request.user, subscriptions, since)
    ret['updates'] = map(prepare_episode_data, episode_updates)

    return JsonResponse(ret)


def get_episode_updates(user, subscribed_podcasts, since):
    """ Returns the episode updates since the timestamp """

    EpisodeStatus = namedtuple('EpisodeStatus', 'episode status action')

    episode_status = {}
    episodes = chain.from_iterable(p.get_episodes(since) for p in subscribed_podcasts)
    for episode in episodes:
        episode_status[episode._id] = EpisodeStatus(episode, 'new', None)

    e_actions = (p.get_episode_states(user.id) for p in subscribed_podcasts)
    e_actions = chain.from_iterable(e_actions)

    for action in e_actions:
        e_id = action['episode_id']

        if e_id in episode_status:
            episode = episode_status[e_id].episode
        else:
            episode = models.Episode.get(e_id)

        episode_status[e_id] = EpisodeStatus(episode, action['action'], action)

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
