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
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, Http404
from django.contrib.auth import authenticate, login, logout
from django.template import RequestContext
from mygpo.api.models import Podcast, UserProfile, Episode, Device, EpisodeAction, SubscriptionAction, ToplistEntry, Subscription, SuggestionEntry, Rating, SyncGroup, SUBSCRIBE_ACTION, UNSUBSCRIBE_ACTION
from mygpo.web.forms import UserAccountForm, DeviceForm, SyncForm
from mygpo.api.opml import Exporter
from django.utils.translation import ugettext as _
from mygpo.api.basic_auth import require_valid_user
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from datetime import datetime
from django.contrib.sites.models import Site
from django.conf import settings
from mygpo.api.sanitizing import sanitize_url
import re

def home(request):
       current_site = Site.objects.get_current()
       if request.user.is_authenticated():
              subscriptionlist = create_subscriptionlist(request)

              return render_to_response('home-user.html', {
                    'subscriptionlist': subscriptionlist,
                    'url': current_site
              }, context_instance=RequestContext(request))

       else:
              podcasts = Podcast.objects.count()
              return render_to_response('home.html', {
                    'podcast_count': podcasts,
                    'url': current_site
              })

def create_subscriptionlist(request):
    #sync all devices first
    for d in Device.objects.filter(user=request.user):
        d.sync()

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

def podcast(request, pid):
    try:
        podcast = Podcast.objects.get(pk=pid)
    except Podcast.DoesNotExist:
        raise Http404('There is no podcast with id %s' % pid)

    if request.user.is_authenticated():        
        devices = Device.objects.filter(user=request.user)
        history = SubscriptionAction.objects.filter(podcast=podcast,device__in=devices).order_by('-timestamp')
        subscribed_devices = [s.device for s in Subscription.objects.filter(podcast=podcast,user=request.user)]
        subscribe_targets = podcast.subscribe_targets(request.user)
        episodes = episode_list(podcast, request.user)
        unsubscribe = '/podcast/' + pid + '/unsubscribe'
        return render_to_response('podcast.html', {
            'history': history,
            'podcast': podcast,
            'devices': subscribed_devices,
            'can_subscribe': len(subscribe_targets) > 0,
            'episodes': episodes,
            'unsubscribe': unsubscribe,
        }, context_instance=RequestContext(request))
    else:
        current_site = Site.objects.get_current()
        return render_to_response('podcast.html', {
            'podcast': podcast,
            'url': current_site
        }, context_instance=RequestContext(request))



def history(request, len=20):
    devices = Device.objects.filter(user=request.user)
    history = SubscriptionAction.objects.filter(device__in=devices).order_by('-timestamp')[:len]
    return render_to_response('history.html', {
        'history': history,
    }, context_instance=RequestContext(request))

def devices(request):
    devices = Device.objects.filter(user=request.user,deleted=False).order_by('sync_group')
    return render_to_response('devicelist.html', {
        'devices': devices,
    }, context_instance=RequestContext(request))

@login_required
def podcast_subscribe(request, pid):
    podcast = Podcast.objects.get(pk=pid)
    error_message = None

    if request.method == 'POST':
        form = SyncForm(request.POST)

        try:
            target = form.get_target()

            if isinstance(target, SyncGroup):
                device = target.devices()[0]
            else:
                device = target

            SubscriptionAction.objects.create(podcast=podcast, device=device, action=SUBSCRIBE_ACTION)

            return HttpResponseRedirect('/podcast/%s' % podcast.id)

        except ValueError, e:
            error_message = _('Could not subscribe to the podcast: %s' % e)

    targets = podcast.subscribe_targets(request.user)

    form = SyncForm()
    form.set_targets(targets, _('With which client do you want to subscribe?'))

    return render_to_response('subscribe.html', {
        'error_message': error_message,
        'podcast': podcast,
        'can_subscribe': len(targets) > 0,
        'form': form
    }, context_instance=RequestContext(request))

@login_required
def podcast_unsubscribe(request, pid, device_id):

    return_to = request.GET.get('return_to')

    if return_to == None:
        raise Http404('Wrong URL')

    podcast = Podcast.objects.get(pk=pid)
    device = Device.objects.get(pk=device_id)
    SubscriptionAction.objects.create(podcast=podcast, device=device, action=UNSUBSCRIBE_ACTION, timestamp=datetime.now())

    return HttpResponseRedirect(return_to)

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


def toplist(request, len=100):
    entries = ToplistEntry.objects.all().order_by('-subscriptions')[:len]
    current_site = Site.objects.get_current()
    return render_to_response('toplist.html', {
        'entries': entries,
        'url': current_site
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

    entries = SuggestionEntry.forUser(request.user)
    current_site = Site.objects.get_current()
    return render_to_response('suggestions.html', {
        'entries': entries,
        'rated'  : rated,
        'url': current_site
    }, context_instance=RequestContext(request))


@login_required
def device(request, device_id):
    device = Device.objects.get(pk=device_id)
    subscriptions = device.get_subscriptions()
    synced_with = list(device.sync_group.devices()) if device.sync_group else []
    if device in synced_with: synced_with.remove(device)
    success = False
    error_message = None
    sync_form = SyncForm()
    sync_form.set_targets(device.sync_targets(), _('Synchronize with the following devices'))

    if request.method == 'POST':
        device_form = DeviceForm(request.POST)

        if device_form.is_valid():
            device.name = device_form.cleaned_data['name']
            device.type = device_form.cleaned_data['type']
            device.uid  = device_form.cleaned_data['uid']
            try:
                device.save()
                success = True
            except IntegrityError, ie:
                device = Device.objects.get(pk=device_id)
                error_message = _('You can\'t use the same UID for two devices.')

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
        'error_message': error_message,
        'subscriptions': subscriptions,
        'synced_with': synced_with,
        'has_sync_targets': len(device.sync_targets()) > 0
    }, context_instance=RequestContext(request))


@login_required
def device_delete(request, device_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    device = Device.objects.get(pk=device_id)
    device.deleted = True
    device.save()

    current_site = Site.objects.get_current()
    subscriptionlist = create_subscriptionlist(request)
    return render_to_response('home-user.html', {
         'subscriptionlist': subscriptionlist,
         'url': current_site,
	  'deletedevice_success': True,
         'device_name': device.name
    }, context_instance=RequestContext(request))


@login_required
def device_sync(request, device_id):

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    form = SyncForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest('invalid')

    try:
        target = form.get_target()

        device = Device.objects.get(pk=device_id)
        device.sync_with(target)

    except ValueError, e:
        log('error while syncing device %s: %s' % (device_id, e))

    return HttpResponseRedirect('/device/%s' % device_id)

@login_required
def device_unsync(request, device_id):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    device = Device.objects.get(pk=device_id)
    device.unsync()

    return HttpResponseRedirect('/device/%s' % device_id)

@login_required
def podcast_subscribe_url(request):
    url = request.GET.get('url')

    if url == None:
        raise Http404('http://my.gpodder.org/subscribe?url=http://www.example.com/podcast.xml')

    url = sanitize_url(url)

    if url == '':
        raise Http404('Please specify a valid url')

    podcast, created = Podcast.objects.get_or_create(url=url)

    return HttpResponseRedirect('/podcast/%d/subscribe' % podcast.pk)


def author(request):
    current_site = Site.objects.get_current()
    return render_to_response('authors.html', {
        'url': current_site
    }, context_instance=RequestContext(request))


