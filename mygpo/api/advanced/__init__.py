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
from mygpo.api.models import Device, Podcast, SubscriptionAction, Episode, EpisodeAction, SUBSCRIBE_ACTION, UNSUBSCRIBE_ACTION, EPISODE_ACTION_TYPES, DEVICE_TYPES, Subscription
from mygpo.api.models.users import EpisodeFavorite
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.sanitizing import sanitize_url
from mygpo.api.advanced.directory import episode_data, podcast_data
from mygpo.api.backend import get_all_subscriptions, get_device
from django.shortcuts import get_object_or_404
from time import mktime, gmtime, strftime
from datetime import datetime
import dateutil.parser
from mygpo.log import log
from mygpo.utils import parse_time, parse_bool
from mygpo.decorators import allowed_methods
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt

try:
    #try to import the JSON module (if we are on Python 2.6)
    import json

    # Python 2.5 seems to have a different json module
    if not 'dumps' in dir(json):
        raise ImportError

except ImportError:
    # No JSON module available - fallback to simplejson (Python < 2.6)
    print "No JSON module available - fallback to simplejson (Python < 2.6)"
    import simplejson as json


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

        since = datetime.fromtimestamp(float(since_))

        changes = get_subscription_changes(request.user, d, since, now)

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
    updated_urls = []
    add_sanitized = []
    rem_sanitized = []

    for a in add:
        if a in remove:
           raise IntegrityError('can not add and remove %s at the same time' % a)

    for u in add:
        us = sanitize_append(u, updated_urls)
        if us != '': add_sanitized.append(us)

    for u in remove:
        us = sanitize_append(u, updated_urls)
        if us != '' and us not in add_sanitized:
            rem_sanitized.append(us)

    for a in add_sanitized:
        p, p_created = Podcast.objects.get_or_create(url=a)
        try:
            p.subscribe(device)
        except IntegrityError, e:
            log('can\'t add subscription %s for user %s: %s' % (a, user, e))

    for r in rem_sanitized:
        p, p_created = Podcast.objects.get_or_create(url=r)
        try:
            p.unsubscribe(device)
        except IntegrityError, e:
            log('can\'t remove subscription %s for user %s: %s' % (r, user, e))

    return updated_urls

def get_subscription_changes(user, device, since, until):
    #ordered by ascending date; newer entries overwriter older ones
    query = SubscriptionAction.objects.filter(device=device,
            timestamp__gt=since, timestamp__lte=until).order_by('timestamp')
    actions = dict([(a.podcast, a) for a in query])

    add = filter(lambda (p, a): a.action == SUBSCRIBE_ACTION, actions.items())
    add = map(lambda (p, a): p.url, add)

    rem = filter(lambda (p, a): a.action == UNSUBSCRIBE_ACTION, actions.items())
    rem = map(lambda (p, a): p.url, rem)

    until_ = int(mktime(until.timetuple()))
    return {'add': add, 'remove': rem, 'timestamp': until_}


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

        since = datetime.fromtimestamp(float(since_)) if since_ else None

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
        us = sanitize_append(e['podcast'], update_urls)
        if us == '': continue

        podcast, p_created = Podcast.objects.get_or_create(url=us)

        eus = sanitize_append(e['episode'], update_urls)
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
    devices = map(device_data, devices)

    return JsonResponse(devices)


def device_data(device):
    return dict(
        id           = device.uid,
        caption      = device.name,
        type         = device.type,
        subscriptions= Subscription.objects.filter(device=device).count()
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

    since = datetime.fromtimestamp(float(since_))

    ret = get_subscription_changes(request.user, device, since, now)

    # replace added urls with details
    podcast_details = []
    for url in ret['add']:
        podcast = Podcast.objects.get(url=url)
        podcast_details.append(podcast_data(podcast))

    ret['add'] = podcast_details


    # add episode details
    subscriptions = get_all_subscriptions(request.user)
    episode_status = {}
    for e in Episode.objects.filter(podcast__in=subscriptions, timestamp__gte=since).order_by('timestamp'):
        episode_status[e] = 'new'
    for a in EpisodeAction.objects.filter(user=request.user, episode__podcast__in=subscriptions, timestamp__gte=since).order_by('timestamp'):
        episode_status[a.episode] = a.action

    updates = []
    for episode, status in episode_status.iteritems():
        t = episode_data(episode)
        t['released'] = e.timestamp.strftime('%Y-%m-%dT%H:%M:%S')
        t['status'] = status
        updates.append(t)

    ret['updates'] = updates

    return JsonResponse(ret)


@require_valid_user
@check_username
def favorites(request, username):
    favorites = [x.episode for x in EpisodeFavorite.objects.filter(user=request.user).order_by('-created')]
    ret = map(episode_data, favorites)
    return JsonResponse(ret)


def sanitize_append(url, sanitized_list):
    urls = sanitize_url(url)
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

