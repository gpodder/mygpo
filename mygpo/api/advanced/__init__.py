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

from mygpo.api.basic_auth import require_valid_user, check_username
from django.http import HttpResponse, HttpResponseBadRequest
from mygpo.api.models import Device, Podcast, Episode, EpisodeAction, SUBSCRIBE_ACTION, UNSUBSCRIBE_ACTION, EPISODE_ACTION_TYPES, DEVICE_TYPES
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.sanitizing import sanitize_url, sanitize_urls
from mygpo.api.advanced.directory import episode_data, podcast_data
from mygpo.api.backend import get_device, get_favorites
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import RequestSite
from time import mktime, gmtime, strftime
from datetime import datetime
import dateutil.parser
from mygpo.log import log
from mygpo.utils import parse_time, parse_bool, get_to_dict
from mygpo.decorators import allowed_methods
from mygpo.core import models
from mygpo.core.models import SanitizingRule
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from mygpo.users.models import PodcastUserState
from mygpo import migrate

try:
    import simplejson as json
except ImportError:
    import json


@csrf_exempt
@require_valid_user
@check_username
@allowed_methods(['GET', 'POST'])
def subscriptions(request, username, device_uid):

    now = datetime.now()
    now_ = int(mktime(now.timetuple()))

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
    podcasts = get_to_dict(models.Podcast, podcast_ids)

    add_urls = [ podcasts[i].url for i in add]
    rem_urls = [ podcasts[i].url for i in rem]

    until_ = int(mktime(until.timetuple()))
    return {'add': add_urls, 'remove': rem_urls, 'timestamp': until_}


@csrf_exempt
@require_valid_user
@check_username
@allowed_methods(['GET', 'POST'])
def episodes(request, username, version=1):

    version = int(version)
    now = datetime.now()
    now_ = int(mktime(now.timetuple()))

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
    if aggregated:
        actions = {}
    else:
        actions = []
    eactions = EpisodeAction.objects.filter(user=user, timestamp__lte=until)

    if podcast:
        eactions = eactions.filter(episode__podcast=podcast)

    if device:
        eactions = eactions.filter(device=device)

    if since: # we can't use None with __gt
        eactions = eactions.filter(timestamp__gt=since)

    if aggregated:
        eactions = eactions.order_by('timestamp')

    for a in eactions:
        action = {
            'podcast': a.episode.podcast.url,
            'episode': a.episode.url,
            'action':  a.action,
            'timestamp': a.timestamp.strftime('%Y-%m-%dT%H:%M:%S') #2009-12-12T09:00:00
        }

        if a.action == 'play' and a.playmark:
            if version == 1:
                t = gmtime(a.playmark)
                action['position'] = strftime('%H:%M:%S', t)
            elif None in (a.playmark, a.started, a.total):
                log('Ignoring broken episode action in DB: %r' % (a,))
                continue
            else:
                action['position'] = int(a.playmark)
                action['started'] = int(a.started)
                action['total'] = int(a.total)

        if aggregated:
            actions[a.episode] = action
        else:
            actions.append(action)

    until_ = int(mktime(until.timetuple()))

    if aggregated:
        actions = list(actions.itervalues())

    return {'actions': actions, 'timestamp': until_}


def update_episodes(user, actions):
    update_urls = []

    for e in actions:
        us = sanitize_append(e['podcast'], 'podcast', update_urls)
        if us == '': continue

        podcast, p_created = Podcast.objects.get_or_create(url=us)

        eus = sanitize_append(e['episode'], 'episode', update_urls)
        if eus == '': continue

        episode, e_created = Episode.objects.get_or_create(podcast=podcast, url=eus)
        action  = e['action']
        if not valid_episodeaction(action):
            raise Exception('invalid action %s' % action)

        if 'device' in e:
            device = get_device(user, e['device'])
        else:
            device = None

        timestamp = dateutil.parser.parse(e['timestamp']) if 'timestamp' in e else datetime.now()

        time_values = check_time_values(e)

        try:
            EpisodeAction.objects.create(user=user, episode=episode,
                    device=device, action=action, timestamp=timestamp,
                    playmark=time_values['position'],
                    started=time_values['started'],
                    total=time_values['total'])
        except Exception, e:
            log('error while adding episode action (user %s, episode %s, device %s, action %s, timestamp %s): %s' % (user, episode, device, action, timestamp, e))

    return update_urls


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
    now_ = int(mktime(now.timetuple()))

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

    # replace added urls with details
    podcast_details = []
    for url in ret['add']:
        podcast = Podcast.objects.get(url=url)
        podcast_details.append(podcast_data(podcast, domain))

    ret['add'] = podcast_details


    # add episode details
    user = migrate.get_or_migrate_user(request.user)
    subscriptions = dev.get_subscribed_podcasts()
    subscriptions_oldpodcasts = [p.get_old_obj() for p in subscriptions]
    episode_status = {}
    for e in Episode.objects.filter(podcast__in=subscriptions_oldpodcasts, timestamp__gte=since).order_by('timestamp'):
        episode_status[e] = 'new'
    for a in EpisodeAction.objects.filter(user=request.user, episode__podcast__in=subscriptions_oldpodcasts, timestamp__gte=since).order_by('timestamp'):
        episode_status[a.episode] = a.action

    updates = []
    for episode, status in episode_status.iteritems():
        t = episode_data(episode, domain)
        t['status'] = status
        updates.append(t)

    ret['updates'] = updates

    return JsonResponse(ret)


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


def check_time_values(action):
    PLAY_ACTION_KEYS = ('position', 'started', 'total')

    # Key found, but must not be supplied (no play action!)
    if action['action'] != 'play':
        for key in PLAY_ACTION_KEYS:
            if key in action:
                raise ValueError('%s only allowed in play actions' % key)

    time_values = dict(map(lambda x: (x, parse_time(action[x]) if x in action else None), PLAY_ACTION_KEYS))

    # Sanity check: If started or total are given, require position
    if (('started' in time_values) or \
        ('total' in time_values)) and \
            (not 'position' in time_values):
        raise ValueError('started and total require position')

    # Sanity check: total and position can only appear together
    if (('total' in time_values) or ('started' in time_values)) and \
        not (('total' in time_values) and ('started' in time_values)):
        raise HttpResponseBadRequest('total and started parameters can only appear together')

    return time_values

