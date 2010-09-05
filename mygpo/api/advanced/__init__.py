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
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404, HttpResponseNotAllowed
from mygpo.api.models import Device, Podcast, SubscriptionAction, Episode, EpisodeAction, SUBSCRIBE_ACTION, UNSUBSCRIBE_ACTION, EPISODE_ACTION_TYPES, DEVICE_TYPES, Subscription
from mygpo.api.models.users import EpisodeFavorite
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.sanitizing import sanitize_url
from mygpo.api.advanced.directory import episode_data, podcast_data
from mygpo.api.backend import get_all_subscriptions
from django.core import serializers
from django.shortcuts import get_object_or_404
from time import mktime, gmtime, strftime
from datetime import datetime, timedelta
import dateutil.parser
from mygpo.log import log
from mygpo.utils import parse_time, parse_bool
from django.db import IntegrityError
import re
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
def subscriptions(request, username, device_uid):

    now = datetime.now()
    now_ = int(mktime(now.timetuple()))

    if request.method == 'GET':
        try:
            d = Device.objects.get(user=request.user, uid=device_uid, deleted=False)
        except Device.DoesNotExist:
            raise Http404('device %s does not exist' % device_uid)

        try:
            since_ = request.GET['since']
        except KeyError:
            return HttpResponseBadRequest('parameter since missing')

        since = datetime.fromtimestamp(float(since_))

        changes = get_subscription_changes(request.user, d, since, now)

        return JsonResponse(changes)

    elif request.method == 'POST':
        d, created = Device.objects.get_or_create(user=request.user, uid=device_uid, defaults = {'type': 'other', 'name': 'New Device'})

        if d.deleted:
            d.deleted = False
            d.save()

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

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])


def update_subscriptions(user, device, add, remove):
    updated_urls = []
    add_sanitized = []
    rem_sanitized = []

    for a in add:
        if a in remove:
           raise IntegrityError('can not add and remove %s at the same time' % a)

    for u in add:
        us = sanitize_url(u)
        if u != us:  updated_urls.append( (u, us) )
        if us != '': add_sanitized.append(us)

    for u in remove:
        us = sanitize_url(u)
        if u != us:  updated_urls.append( (u, us) )
        if us != '' and us not in add_sanitized:
            rem_sanitized.append(us)

    for a in add_sanitized:
        p, p_created = Podcast.objects.get_or_create(url=a)
        try:
            s = SubscriptionAction.objects.create(podcast=p,device=device,action=SUBSCRIBE_ACTION)
        except IntegrityError, e:
            log('can\'t add subscription %s for user %s: %s' % (a, user, e))

    for r in rem_sanitized:
        p, p_created = Podcast.objects.get_or_create(url=r)
        try:
            s = SubscriptionAction.objects.create(podcast=p,device=device,action=UNSUBSCRIBE_ACTION)
        except IntegrityError, e:
            log('can\'t remove subscription %s for user %s: %s' % (r, user, e))

    return updated_urls

def get_subscription_changes(user, device, since, until):
    actions = {}
    for a in SubscriptionAction.objects.filter(device=device, timestamp__gt=since, timestamp__lte=until).order_by('timestamp'):
        #ordered by ascending date; newer entries overwriter older ones
        actions[a.podcast] = a

    add = []
    remove = []

    for a in actions.values():
        if a.action == SUBSCRIBE_ACTION:
            add.append(a.podcast.url)
        elif a.action == UNSUBSCRIBE_ACTION:
            remove.append(a.podcast.url)

    until_ = int(mktime(until.timetuple()))
    return {'add': add, 'remove': remove, 'timestamp': until_}


@csrf_exempt
@require_valid_user
@check_username
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

        try:
            podcast = Podcast.objects.get(url=podcast_url) if podcast_url else None
            device  = Device.objects.get(user=request.user,uid=device_uid, deleted=False) if device_uid else None
        except:
            raise Http404

        return JsonResponse(get_episode_changes(request.user, podcast, device, since, now, aggregated, version))

    else:
        return HttpResponseNotAllowed(['POST', 'GET'])


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
        u = e['podcast']
        us = sanitize_url(u)
        if u != us:  update_urls.append( (u, us) )
        if us == '': continue

        podcast, p_created = Podcast.objects.get_or_create(url=us)

        eu = e['episode']
        eus = sanitize_url(eu, podcast=False, episode=True)
        if eu != eus: update_urls.append( (eu, eus) )
        if eus == '': continue

        episode, e_created = Episode.objects.get_or_create(podcast=podcast, url=eus)
        action  = e['action']
        if not valid_episodeaction(action):
            raise Exception('invalid action %s' % action)

        if 'device' in e:
            device, created = Device.objects.get_or_create(user=user, uid=e['device'], defaults={'name': 'Unknown', 'type': 'other'})

            # undelete a previously deleted device
            if device.deleted:
                device.deleted = False
                device.save()

        else:
            device, created = None, False

        timestamp = dateutil.parser.parse(e['timestamp']) if 'timestamp' in e and e['timestamp'] else datetime.now()

        # Time values for play actions and their keys in JSON
        PLAY_ACTION_KEYS = ('position', 'started', 'total')
        time_values = {}

        for key in PLAY_ACTION_KEYS:
            if key in e:
                if action != 'play':
                    # Key found, but must not be supplied (no play action!)
                    return HttpResponseBadRequest('%s only allowed in play actions' % key)

                try:
                    time_values[key] = parse_time(e[key])
                except ValueError:
                    log('could not parse %s parameter (value: %s) for user %s' % (key, repr(e[key]), user))
                    return HttpResponseBadRequest('Wrong format for %s: %s' % (key, repr(e[key])))
            else:
                # Value not supplied by client
                time_values[key] = None

        # Sanity check: If started or total are given, require position
        if (time_values['started'] is not None or \
                time_values['total'] is not None) and \
                time_values['position'] is None:
            return HttpResponseBadRequest('started and total require position')

        # Sanity check: total and position can only appear together
        if (time_values['total'] or time_values['started']) and \
            not (time_values['total'] and time_values['started']):
            return HttpResponseBadRequest('total and started parameters can only appear together')

        try:
            EpisodeAction.objects.create(user=user, episode=episode, device=device, action=action, timestamp=timestamp,
                    playmark=time_values['position'], started=time_values['started'], total=time_values['total'])
        except Exception, e:
            log('error while adding episode action (user %s, episode %s, device %s, action %s, timestamp %s): %s' % (user, episode, device, action, timestamp, e))

    return update_urls


@csrf_exempt
@require_valid_user
@check_username
def device(request, username, device_uid):

    # Workaround for mygpoclient 1.0: It uses "PUT" requests
    # instead of "POST" requests for uploading device settings
    if request.method in ('POST', 'PUT'):
        d, created = Device.objects.get_or_create(user=request.user, uid=device_uid)

        #undelete a previously deleted device
        if d.deleted:
            d.deleted = False
            d.save()

        data = json.loads(request.raw_post_data)

        if 'caption' in data:
            d.name = data['caption']

        if 'type' in data:
            if not valid_devicetype(data['type']):
                return HttpResponseBadRequest('invalid device type %s' % data['type'])
            d.type = data['type']

        d.save()

        return HttpResponse()

    else:
        return HttpResponseNotAllowed(['POST'])

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
def devices(request, username):

    if request.method == 'GET':
        devices = []
        for d in Device.objects.filter(user=request.user, deleted=False):
            devices.append({
                'id': d.uid,
                'caption': d.name,
                'type': d.type,
                'subscriptions': Subscription.objects.filter(device=d).count()
            })

        return JsonResponse(devices)

    else:
        return HttpResponseNotAllowed(['GET'])


@csrf_exempt
@require_valid_user
@check_username
def updates(request, username, device_uid):
    now = datetime.now()
    now_ = int(mktime(now.timetuple()))

    device = get_object_or_404(Device, user=request.user, uid=device_uid)

    try:
        since_ = request.GET['since']
    except KeyError:
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

