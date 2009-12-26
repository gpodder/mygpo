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

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from mygpo.api.models import Podcast, UserProfile, Episode, Device, EpisodeAction, SubscriptionAction, ToplistEntry, Subscription, SuggestionEntry, Rating, SyncGroup
from mygpo.web.forms import UserAccountForm, DeviceForm, SyncForm
from mygpo.api.opml import Exporter
from django.utils.translation import ugettext as _
from mygpo.api.basic_auth import require_valid_user
from django.contrib.auth.decorators import login_required
from datetime import datetime
import re

def home(request):
       if request.user.is_authenticated():
              subscriptionlist = create_subscriptionlist(request)              

              return render_to_response('home-user.html', {
                    'subscriptionlist': subscriptionlist
              }, context_instance=RequestContext(request))

       else:
              podcasts = Podcast.objects.count()
              return render_to_response('home.html', {
                    'podcast_count': podcasts
              })

def create_subscriptionlist(request):
    subscriptions = Subscription.objects.filter(user=request.user)
    l = {}
    for s in subscriptions:
        if s.podcast in l:
            l[s.podcast]['devices'].append(s.device)
        else:
            e = Episode.objects.filter(podcast=s.podcast).order_by('-timestamp')
            episode = e[0] if e.count() > 0 else None
            devices = [s.device]
            l[s.podcast] = {'podcast': s.podcast, 'episode': episode, 'devices': devices}

    return l.values()


@login_required
def podcast(request, pid):
    podcast = Podcast.objects.get(pk=pid)
    devices = Device.objects.filter(user=request.user)
    history = SubscriptionAction.objects.filter(podcast=podcast,device__in=devices).order_by('-timestamp')
    subscribed_devices = [s.device for s in Subscription.objects.filter(podcast=podcast,user=request.user)]
    episodes = episode_list(podcast, request.user)
    return render_to_response('podcast.html', {
        'history': history,
        'podcast': podcast,
        'devices': subscribed_devices,
        'episodes': episodes,
    }, context_instance=RequestContext(request))

def episode_list(podcast, user):
    list = {}
    episodes = Episode.objects.filter(podcast=podcast).order_by('-timestamp')
    for e in episodes:
        list[e] = None
        for action in EpisodeAction.objects.filter(episode=e, user=user).order_by('timestamp'):
            list[e] = action

    return list

@login_required
def episode(request, id):
    episode = Episode.objects.get(pk=id)
    history = EpisodeAction.objects.filter(user=request.user, episode=episode).order_by('-timestamp')

    return render_to_response('episode.html', {
        'episode': episode,
        'history': history,
    }, context_instance=RequestContext(request))


@login_required
def account(request):
    success = False

    if request.method == 'POST':
        form = UserAccountForm(request.POST)

        if form.is_valid():
            request.user.email = form.cleaned_data['email']
            request.user.save()
            request.user.get_profile().public_profile = form.cleaned_data['public']
            request.user.get_profile().save()

            success = True

    else:
        form = UserAccountForm({
            'email': request.user.email,
            'public': request.user.get_profile().public_profile
            })

    return render_to_response('account.html', {
        'form': form,
        'success': success
    }, context_instance=RequestContext(request))


def toplist(request):
    len = 30
    entries = ToplistEntry.objects.all().order_by('-subscriptions')[:len]
    return render_to_response('toplist.html', {
        'count'  : len,
        'entries': entries,
    }, context_instance=RequestContext(request))


def toplist_opml(request, count):
    entries = ToplistEntry.objects.all().order_by('-subscriptions')[:count]
    exporter = Exporter(_('my.gpodder.org - Top %s') % count)

    opml = exporter.generate([e.podcast for e in entries])

    return HttpResponse(opml, mimetype='text/xml')
 

@login_required
def suggestions(request):

    rated = False

    if 'rate' in request.GET:
        Rating.objects.create(target='suggestions', user=request.user, rating=request.GET['rate'], timestamp=datetime.now())
        rated = True

    entries = SuggestionEntry.objects.filter(user=request.user).order_by('-priority')
    return render_to_response('suggestions.html', {
        'entries': entries,
        'rated'  : rated
    }, context_instance=RequestContext(request))


@require_valid_user
def suggestions_opml(request, count):
    entries = SuggestionEntry.objects.filter(user=request.user).order_by('-priority')
    exporter = Exporter(_('my.gpodder.org - %s Suggestions') % count)

    opml = exporter.generate([e.podcast for e in entries])

    return HttpResponse(opml, mimetype='text/xml')

def device(request, device_id):
    device = Device.objects.get(pk=device_id)
    subscriptions = device.get_subscriptions()
    synced_with = list(device.sync_group.devices()) if device.sync_group else []
    if device in synced_with: synced_with.remove(device)
    success = False
    sync_form = SyncForm()
    sync_form.set_device(device)

    if request.method == 'POST':
        device_form = DeviceForm(request.POST)

        if device_form.is_valid():
            device.name = device_form.cleaned_data['name']
            device.type = device_form.cleaned_data['type']
            device.uid  = device_form.cleaned_data['uid']
            device.save()
            success = True

    else:
        device_form = DeviceForm({
            'name': device.name,
            'type': device.type,
            'uid' : device.uid
            })

    return render_to_response('device.html', {
        'device': device,
        'device_form': device_form,
        'sync_form': sync_form,
        'success': success,
        'subscriptions': subscriptions,
        'synced_with': synced_with,
        'has_sync_targets': len(device.sync_targets()) > 0
    }, context_instance=RequestContext(request))


def device_sync(request, device_id):

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
        
    form = SyncForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest('invalid')

    target = form.cleaned_data['targets']

    m = re.match('^([dg])(\d+)$', target)
    if m == None:
        return HttpResponseBadRequest()

    if m.group(1) == 'd':
        target = Device.objects.get(pk=m.group(2))
    else:
        target = SyncGroup.objects.get(pk=m.group(2))

    device = Device.objects.get(pk=device_id)

    device.sync_with(target)

    return HttpResponseRedirect('/device/%s' % device_id)


def device_unsync(request, device_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    device = Device.objects.get(pk=device_id)
    device.unsync()

    return HttpResponseRedirect('/device/%s' % device_id)

