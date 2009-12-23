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

from mygpo.api.basic_auth import require_valid_user
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404, HttpResponseNotAllowed
from mygpo.api.models import Device, Podcast, SubscriptionAction, Episode, EpisodeAction, SUBSCRIBE_ACTION, UNSUBSCRIBE_ACTION, EPISODE_ACTION_TYPES, DEVICE_TYPES, Subscription
from mygpo.api.httpresponse import JsonResponse
from django.core import serializers
from time import mktime
from datetime import datetime, timedelta
import dateutil.parser
from mygpo.logging import log
from django.db import IntegrityError
import re

try:
    #try to import the JSON module (if we are on Python 2.6)
    import json
except ImportError:
    # No JSON module available - fallback to simplejson (Python < 2.6)
    print "No JSON module available - fallback to simplejson (Python < 2.6)"
    import simplejson as json

@require_valid_user
def subscriptions(request, username, device_uid):

    if request.user.username != username:
        return HttpResponseForbidden()

    now = datetime.now()
    now_ = int(mktime(now.timetuple()))

    if request.method == 'GET':
        try:
            d = Device.objects.get(user=request.user, uid=device_uid)
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
        d, created = Device.objects.get_or_create(user=request.user, uid=device_uid)

        actions = json.loads(request.POST['data'])
        add = actions['add'] if 'add' in actions else []
        rem = actions['remove'] if 'remove' in actions else []

        for a in add:
            if a in rem:
                return HttpResponseBadRequest('can not add and remove %s at the same time' % a)

        update_subscriptions(request.user, d, add, rem)

        return JsonResponse({'timestamp': now_})

    else:
        return HttpResponseNotAllowed(['GET', 'POST'])


def update_subscriptions(user, device, add, remove):
    for a in add:
        p, p_created = Podcast.objects.get_or_create(url=a)
        try:
            s = SubscriptionAction.objects.create(podcast=p,device=device,action=SUBSCRIBE_ACTION)
        except IntegrityError, e:
            log('can\'t add subscription %s for user %s: %s' % (a, user, e))

    for r in remove:
        p, p_created = Podcast.objects.get_or_create(url=r)
        try:
            s = SubscriptionAction.objects.create(podcast=p,device=device,action=UNSUBSCRIBE_ACTION)
        except IntegrityError, e:
            log('can\'t remove subscription %s for user %s: %s' % (r, user, e))


def get_subscription_changes(user, device, since, until):
    actions = {}
    for a in SubscriptionAction.objects.filter(device=device, timestamp__gt=since, timestamp__lt=until).order_by('timestamp'):
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


@require_valid_user
def episodes(request, username):

    if request.user.username != username:
        return HttpResponseForbidden()

    now = int(mktime(datetime.now().timetuple()))

    if request.method == 'POST':
        try:
            actions = json.loads(request.POST['data'])
        except KeyError:
            return HttpResponseBadRequest()

        update_episodes(request.user, actions)
        return HttpResponse()

    elif request.method == 'GET':
        podcast_id = request.GET.get('podcast', None)
        device_id  = request.GET.get('device', None)
        since      = request.GET.get('since', None)

        try:
            podcast = Podcast.objects.get(pk=podcast_id) if podcast_id else None
            device  = Device.objects.get(pk=device_id) if device_id else None
        except:
            raise Http404

        return JsonRequest(get_episode_changes(request.user, podcast, device, since, now))

    else:
        return HttpResponseNotAllowed(['POST', 'GET'])


def get_episode_changes(user, podcast, device, since, until):
    actions = []
    for a in EpisodeAction.objects.filter(user=user, podcast=podcast, device=device, timestamp__gt=since, timestamp__lt=until):
        action = {
            'podcast': a.episode.podcast.url,
            'episode': a.episode.url,
            'action':  a.action,
            'timestamp': a.timestamp
        }

        if a.action == 'play': action['time'] = a.playmark

        actions.append(action)

    return {'timestamp': since, 'actions': actions}


def update_episodes(user, actions):
    for e in actions:
        try:
            podcast, p_created = Podcast.objects.get_or_create(url=e['podcast'])
            episode, e_created = Episode.objects.get_or_create(podcast=podcast, url=e['episode'])
            action  = e['action']
            if not valid_episodeaction(action):
                return HttpResponseBadRequest('invalid action %s' % action)
        except:
            return HttpResponseBadRequest('not all required fields (podcast, episode, action) given')

        device, created = Device.objects.get_or_create(user=user, uid=e['device'], defaults={'name': 'Unknown', 'type': 'other'}) if 'device' in e else None
        timestamp = dateutil.parser.parse(e['timestamp']) if 'timestamp' in e else None
        position = parseTimeDelta(e['position']) if 'position' in e else None
        playmark = position['seconds'] if position else None

        if position and action != 'play':
            return HttpResponseBadRequest('parameter position can only be used with action play')

        EpisodeAction.objects.create(user=user, episode=episode, device=device, action=action, timestamp=timestamp, playmark=playmark)



@require_valid_user
def device(request, username, device_uid):

    if request.user.username != username:
        return HttpResponseForbidden()

    if request.method == 'POST':
        d, created = Device.objects.get_or_create(user=request.user, uid=device_uid)

        data = json.loads(request.POST['data'])

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

# http://kbyanc.blogspot.com/2007/08/python-reconstructing-timedeltas-from.html
def parseTimeDelta(s):
    """Create timedelta object representing time delta
       expressed in a string
   
    Takes a string in the format produced by calling str() on
    a python timedelta object and returns a timedelta instance
    that would produce that string.
   
    Acceptable formats are: "X days, HH:MM:SS" or "HH:MM:SS".
    """
    if s is None:
        return None
    d = re.match(
            r'((?P<days>\d+) days, )?(?P<hours>\d+):'
            r'(?P<minutes>\d+):(?P<seconds>\d+)',
            str(s)).groupdict(0)
    return timedelta(**dict(( (key, int(value))
                              for key, value in d.items() )))

@require_valid_user
def devices(request, username):

    if request.user.username != username:
        return HttpResponseForbidden()

    if request.method == 'GET':
        devices = []
        for d in Device.objects.filter(user=request.user):
            devices.append({
                'id': d.uid,
                'caption': d.name,
                'type': d.type,
                'subscriptions': Subscription.objects.filter(device=d).count()
            })

        return JsonResponse(devices)

    else:
        return HttpResponseNotAllowed(['GET'])

