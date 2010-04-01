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
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, Http404, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.template import RequestContext
from mygpo.api.models import Podcast, Episode, Device, EpisodeAction, SubscriptionAction, ToplistEntry, EpisodeToplistEntry, Subscription, SuggestionEntry, SyncGroup, SUBSCRIBE_ACTION, UNSUBSCRIBE_ACTION, SubscriptionMeta
from mygpo.data.models import Listener
from mygpo.web.models import Rating, SecurityToken
from mygpo.web.forms import UserAccountForm, DeviceForm, SyncForm, PrivacyForm, ResendActivationForm
from django.forms import ValidationError
from mygpo.api.opml import Exporter
from django.utils.translation import ugettext as _
from mygpo.api.basic_auth import require_valid_user
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from datetime import datetime, date, timedelta
from django.contrib.sites.models import Site
from django.conf import settings
from registration.models import RegistrationProfile
from sets import Set
from mygpo.api.sanitizing import sanitize_url
from mygpo.web.users import get_user
from mygpo.log import log
from mygpo.utils import daterange
from mygpo.constants import PODCAST_LOGO_SIZE, PODCAST_LOGO_BIG_SIZE
import re
import random
import string
import os
import Image
import ImageDraw
import StringIO

def home(request):
    current_site = Site.objects.get_current()
    podcasts = Podcast.objects.count()
    return render_to_response('home.html', {
          'podcast_count': podcasts,
          'url': current_site
    }, context_instance=RequestContext(request))


def cover_art(request, size, filename):
    size = int(size)
    if size not in (PODCAST_LOGO_SIZE, PODCAST_LOGO_BIG_SIZE):
        raise http404('Wrong size')

    # XXX: Is there a "cleaner" way to get the root directory of the installation?
    root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
    target = os.path.join(root, 'htdocs', 'media', 'logo', str(size), filename+'.jpg')
    filename = os.path.join(root, 'htdocs', 'media', 'logo', filename)

    if os.path.exists(filename):
        target_dir = os.path.dirname(target)
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)

        try:
            im = Image.open(filename)
            if im.mode not in ('RGB', 'RGBA'):
                im = im.convert('RGB')
        except:
            raise http404('Cannot open cover file')

        resized = im.resize((size, size), Image.ANTIALIAS)

        # If it's a RGBA image, composite it onto a white background for JPEG
        if resized.mode == 'RGBA':
            background = Image.new('RGB', resized.size)
            draw = ImageDraw.Draw(background)
            draw.rectangle((-1, -1, resized.size[0]+1, resized.size[1]+1), \
                    fill=(255, 255, 255))
            del draw
            resized = Image.composite(resized, background, resized)

        io = StringIO.StringIO()
        resized.save(io, 'JPEG', optimize=True, progression=True, quality=80)
        s = io.getvalue()

        fp = open(target, 'wb')
        fp.write(s)
        fp.close()

        return HttpResponse(s, mimetype='image/jpeg')
    else:
        raise Http404('Cover art not available')

@login_required
def subscriptions(request):
    current_site = Site.objects.get_current()
    subscriptionlist = create_subscriptionlist(request)
    return render_to_response('subscriptions.html', {
        'subscriptionlist': subscriptionlist,
        'url': current_site
    }, context_instance=RequestContext(request))

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
            e = Episode.objects.filter(podcast=s.podcast, timestamp__isnull=False).order_by('-timestamp')
            episode = e[0] if e.count() > 0 else None
            devices = [s.device]
            l[s.podcast] = {'podcast': s.podcast, 'episode': episode, 'devices': devices}

    return l.values()

def podcast(request, pid):
    podcast = get_object_or_404(Podcast, pk=pid)

    if request.user.is_authenticated():        
        devices = Device.objects.filter(user=request.user)
        history = SubscriptionAction.objects.filter(podcast=podcast,device__in=devices).order_by('-timestamp')
        subscribed_devices = [s.device for s in Subscription.objects.filter(podcast=podcast,user=request.user)]
        subscribe_targets = podcast.subscribe_targets(request.user)
        episodes = episode_list(podcast, request.user)
        max_listeners = max([x.listeners for x in episodes]) if len(episodes) else 0
        success = False


        qs = Subscription.objects.filter(podcast=podcast, user=request.user)
        if qs.count()>0 and request.user.get_profile().public_profile:
            # subscription meta is valid for all subscriptions, so we get one - doesn't matter which
            subscription = qs[0]
            subscriptionmeta = subscription.get_meta()
            if request.method == 'POST':
                privacy_form = PrivacyForm(request.POST)
                if privacy_form.is_valid():
                    subscriptionmeta.public = privacy_form.cleaned_data['public']
                    try:
                       subscriptionmeta.save()
                       success = True
                    except IntegrityError, ie:
                       error_message = _('You can\'t use the same UID for two devices.')
            else:
                privacy_form = PrivacyForm({
                    'public': subscriptionmeta.public
                })

        else:
            privacy_form = None

        timeline_data = listener_data(podcast)

        return render_to_response('podcast.html', {
            'history': history,
            'timeline_data': timeline_data,
            'podcast': podcast,
            'privacy_form': privacy_form,
            'devices': subscribed_devices,
            'can_subscribe': len(subscribe_targets) > 0,
            'episodes': episodes,
            'max_listeners': max_listeners,
            'success': success
        }, context_instance=RequestContext(request))
    else:
        current_site = Site.objects.get_current()
        return render_to_response('podcast.html', {
            'podcast': podcast,
            'url': current_site
        }, context_instance=RequestContext(request))

def listener_data(podcast):
    d = date(2010, 1, 1)
    day = timedelta(1)
    episodes = EpisodeAction.objects.filter(episode__podcast=podcast, timestamp__gte=d).order_by('timestamp').values('timestamp')
    if len(episodes) == 0:
        return []

    start = episodes[0]['timestamp']

    days = []
    for d in daterange(start):
        next = d + timedelta(days=1)
        listeners = EpisodeAction.objects.filter(episode__podcast=podcast, timestamp__gte=d, timestamp__lt=next).values('user_id').distinct().count()
        e = Episode.objects.filter(podcast=podcast, timestamp__gte=d, timestamp__lt=next)
        episode = e[0] if e.count() > 0 else None
        days.append({
            'date': d,
            'listeners': listeners,
            'episode': episode})

    return days

def history(request, len=15, device_id=None):
    if device_id:
        devices = Device.objects.filter(id=device_id)
    else:
        devices = Device.objects.filter(user=request.user)

    history = SubscriptionAction.objects.filter(device__in=devices).order_by('-timestamp')[:len]
    episodehistory = EpisodeAction.objects.filter(device__in=devices).order_by('-timestamp')[:len]

    generalhistory = []

    for row in history:
        generalhistory.append(row)
    for row in episodehistory:
        generalhistory.append(row)

    generalhistory.sort(key=lambda x: x.timestamp,reverse=True)

    return render_to_response('history.html', {
        'generalhistory': generalhistory,
        'singledevice': devices[0] if device_id else None
    }, context_instance=RequestContext(request))


@login_required
def devices(request):
    devices = Device.objects.filter(user=request.user,deleted=False).order_by('sync_group')
    return render_to_response('devicelist.html', {
        'devices': devices,
    }, context_instance=RequestContext(request))


@login_required
def podcast_subscribe(request, pid):
    podcast = get_object_or_404(Podcast, pk=pid)
    error_message = None

    if request.method == 'POST':
        form = SyncForm(request.POST)

        try:
            target = form.get_target()

            if isinstance(target, SyncGroup):
                device = target.devices()[0]
            else:
                device = target

            try:
                SubscriptionAction.objects.create(podcast=podcast, device=device, action=SUBSCRIBE_ACTION)
            except IntegrityError, e:
                log('error while subscribing to podcast (device %s, podcast %s)' % (device.id, podcast.id))

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

    podcast = get_object_or_404(Podcast, pk=pid)
    device = Device.objects.get(pk=device_id)
    try:
        SubscriptionAction.objects.create(podcast=podcast, device=device, action=UNSUBSCRIBE_ACTION, timestamp=datetime.now())
    except IntegrityError, e:
        log('error while unsubscribing from podcast (device %s, podcast %s)' % (device.id, podcast.id))

    return HttpResponseRedirect(return_to)

def episode_list(podcast, user):
    """
    Returns a list of episodes, with their action-attribute set to the latest
    action. The attribute is unsert if there is no episode-action for
    the episode.
    """
    episodes = Episode.objects.filter(podcast=podcast).order_by('-timestamp')
    for e in episodes:
        listeners = Listener.objects.filter(episode=e).values('user').distinct()
        e.listeners = listeners.count()

        if user.is_authenticated():
            actions = EpisodeAction.objects.filter(episode=e, user=user).order_by('-timestamp')
            if actions.count() > 0:
                e.action = actions[0]

    return episodes


@login_required
def account(request):
    success = False
    error_message = ''
    site = Site.objects.get_current()
    token, c = SecurityToken.objects.get_or_create(user=request.user, object='subscriptions', action='r',
        defaults = {'token': "".join(random.sample(string.letters+string.digits, 32))})


    if request.method == 'GET':

        if 'public_subscriptions' in request.GET:
            token.token = ''
            token.save()

        elif 'private_subscriptions' in request.GET:
            token.token = "".join(random.sample(string.letters+string.digits, 32))
            token.save()

        form = UserAccountForm({
            'email': request.user.email,
            'public': request.user.get_profile().public_profile
            })

        return render_to_response('account.html', {
            'site': site,
            'token': token.token,
            'form': form,
            }, context_instance=RequestContext(request))

    try:
        form = UserAccountForm(request.POST)

        if not form.is_valid():
            raise ValueError(_('Oops! Something went wrong. Please double-check the data you entered.'))

        if form.cleaned_data['password_current']:
            if not request.user.check_password(form.cleaned_data['password_current']):
                raise ValueError('Current password is incorrect')

            request.user.set_password(form.cleaned_data['password1'])

        request.user.email = form.cleaned_data['email']
        request.user.save()
        request.user.get_profile().public_profile = form.cleaned_data['public']
        request.user.get_profile().save()

        success = True

    except ValueError, e:
        success = False
        error_message = e

    except ValidationError, e:
        success = False
        error_message = e

    return render_to_response('account.html', {
        'site': site,
        'token': token.token,
        'form': form,
        'success': success,
        'error_message': error_message
    }, context_instance=RequestContext(request))


def toplist(request, len=100):
    entries = ToplistEntry.objects.all().order_by('-subscriptions')[:len]
    max_subscribers = max([e.subscriptions for e in entries])
    current_site = Site.objects.get_current()
    return render_to_response('toplist.html', {
        'entries': entries,
        'max_subscribers': max_subscribers,
        'url': current_site
    }, context_instance=RequestContext(request))


def episode_toplist(request, len=100):
    entries = EpisodeToplistEntry.objects.all().order_by('-listeners')[:len]
    current_site = Site.objects.get_current()

    # Determine maximum listener amount (or 0 if no entries exist)
    max_listeners = max([0]+[e.listeners for e in entries])

    return render_to_response('episode_toplist.html', {
        'entries': entries,
        'max_listeners': max_listeners,
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

    if device.user != request.user:
        return HttpResponseForbidden(_('You are not allowed to access this device'))

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

@login_required
def delete_account(request):

    if request.method == 'GET':
        return render_to_response('delete_account.html')

    request.user.is_active = False
    request.user.save()
    logout(request)
    return render_to_response('delete_account.html', {
        'success': True
        })

def author(request):
    current_site = Site.objects.get_current()
    return render_to_response('authors.html', {
        'url': current_site
    }, context_instance=RequestContext(request))


def resend_activation(request):
    error_message = ''

    if request.method == 'GET':
        form = ResendActivationForm()
        return render_to_response('registration/resend_activation.html', {
            'form': form,
        })

    site = Site.objects.get_current()
    form = ResendActivationForm(request.POST)

    try:
        if not form.is_valid():
            raise ValueError(_('Invalid Username entered'))

        try:
            user = get_user(form.cleaned_data['username'], form.cleaned_data['email'])
        except User.DoesNotExist:
            raise ValueError(_('User does not exist.'))

        try:
            profile = RegistrationProfile.objects.get(user=user)
        except RegistrationProfile.DoesNotExist:
            profile = RegistrationProfile.objects.create_profile(user)

        if profile.activation_key == RegistrationProfile.ACTIVATED:
            raise ValueError(_('Your account already has been activated. Go ahead and log in.'))

        elif profile.activation_key_expired():
            raise ValueError(_('Your activation key has expired. Please try another username, or retry with the same one tomorrow.'))

    except ValueError, e:
        return render_to_response('registration/resend_activation.html', {
           'form': form,
           'error_message' : e
        })


    try:
        profile.send_activation_email(site)

    except AttributeError:
        #old versions of django-registration send registration mails from RegistrationManager
        RegistrationProfile.objects.send_activation_email(profile, site)

    return render_to_response('registration/resent_activation.html')


def user_subscriptions(request, username):
    user = get_object_or_404(User, username=username)

    token, c = SecurityToken.objects.get_or_create(user=user, object='subscriptions', action='r',
        defaults = {'token': "".join(random.sample(string.letters+string.digits, 32))})

    u_token = request.GET.get('token', '')
    if token.token == '' or token.token == u_token:
        subscriptions = [s for s in Subscription.objects.filter(user=user)]
        public_subscriptions = set([s.podcast for s in subscriptions if s.get_meta().public])
        return render_to_response('user_subscriptions.html', {
            'subscriptions': public_subscriptions,
            'other_user': user})

    else:
        return render_to_response('user_subscriptions_denied.html', {
            'other_user': user})

