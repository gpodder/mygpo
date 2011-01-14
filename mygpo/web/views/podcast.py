from datetime import date, timedelta, datetime

from django.http import HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from django.utils.translation import ugettext as _
from mygpo.api.models import Podcast, Episode, EpisodeAction, Device, SubscriptionAction, Subscription, SyncGroup
from mygpo.api.sanitizing import sanitize_url
from mygpo.web.forms import PrivacyForm, SyncForm
from mygpo.data.models import Listener, PodcastTag
from mygpo.decorators import manual_gc, allowed_methods
from mygpo.utils import daterange
from mygpo.log import log

MAX_TAGS_ON_PAGE=50


@allowed_methods(['GET', 'POST'])
def show(request, pid):
    podcast = get_object_or_404(Podcast, pk=pid)
    episodes = episode_list(podcast, request.user)
    max_listeners = max([x.listener_count() for x in episodes]) if len(episodes) else 0
    related_podcasts = [x for x in podcast.group.podcasts() if x != podcast] if podcast.group else []

    tags = get_tags(podcast, request.user)

    if request.user.is_authenticated():
        devices = Device.objects.filter(user=request.user)
        history = SubscriptionAction.objects.filter(podcast=podcast,device__in=devices).order_by('-timestamp')
        subscribed_devices = [s.device for s in Subscription.objects.filter(podcast=podcast,user=request.user)]
        subscribe_targets = podcast.subscribe_targets(request.user)
        success = False


        qs = Subscription.objects.filter(podcast=podcast, user=request.user)
        if qs.count()>0 and request.user.get_profile().public_profile:
            # subscription meta is valid for all subscriptions, so we get one - doesn't matter which
            subscription = qs[0]
            subscriptionmeta = subscription.get_meta()
            if request.method == 'POST':
                privacy_form = PrivacyForm(request.POST)
                if privacy_form.is_valid():
                    subscriptionmeta.settings['public_subscription'] = privacy_form.cleaned_data['public']
                    try:
                       subscriptionmeta.save()
                       success = True
                    except IntegrityError, ie:
                       error_message = _('You can\'t use the same Device ID for two devices.')
            else:
                privacy_form = PrivacyForm({
                    'public': subscriptionmeta.public
                })

        else:
            privacy_form = None

        subscribe_form = SyncForm()
        subscribe_form.set_targets(subscribe_targets, '')

        timeline_data = listener_data(podcast)
        return render_to_response('podcast.html', {
            'tags': tags,
            'history': history,
            'timeline_data': timeline_data,
            'podcast': podcast,
            'privacy_form': privacy_form,
            'devices': subscribed_devices,
            'related_podcasts': related_podcasts,
            'can_subscribe': len(subscribe_targets) > 0,
            'subscribe_form': subscribe_form,
            'episodes': episodes,
            'max_listeners': max_listeners,
            'success': success
        }, context_instance=RequestContext(request))
    else:
        current_site = RequestSite(request)
        return render_to_response('podcast.html', {
            'podcast': podcast,
            'related_podcasts': related_podcasts,
            'tags': tags,
            'url': current_site,
            'episodes': episodes,
            'max_listeners': max_listeners,
        }, context_instance=RequestContext(request))


def get_tags(podcast, user):
    tags = {}
    for t in PodcastTag.objects.filter(podcast=podcast).values('tag').distinct():
        tag_str = t['tag'].lower()
        tags[tag_str] = False

    if not user.is_anonymous():
        for t in PodcastTag.objects.filter(podcast=podcast, user=user).values('tag').distinct():
            tag_str = t['tag'].lower()
            tags[tag_str] = True

    tag_list = [{'tag': key, 'is_own': value} for key, value in tags.iteritems()]
    tag_list.sort(key=lambda x: x['tag'])

    if len(tag_list) > MAX_TAGS_ON_PAGE:
        tag_list = filter(lambda x: x['is_own'], tag_list)
        tag_list.append({'tag': '...', 'is_own': False})

    return tag_list


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


def episode_list(podcast, user):
    """
    Returns a list of episodes, with their action-attribute set to the latest
    action. The attribute is unsert if there is no episode-action for
    the episode.
    """
    episodes = podcast.get_episodes().order_by('-timestamp')
    for e in episodes:
        if user.is_authenticated():
            actions = EpisodeAction.objects.filter(episode=e, user=user).order_by('-timestamp')
            if actions.count() > 0:
                e.action = actions[0]

    return episodes


@login_required
def add_tag(request, pid):
    podcast = get_object_or_404(Podcast, id=pid)
    tag_str = request.GET.get('tag', '')
    if not tag_str:
        return HttpResponseBadRequest()

    tags = tag_str.split(',')
    for t in tags:
        t = t.strip()
        tag = PodcastTag.objects.get_or_create(podcast=podcast, tag=t, source='user', user=request.user)

    if request.GET.get('next', '') == 'mytags':
        return HttpResponseRedirect('/tags/')

    return HttpResponseRedirect('/podcast/%s' % pid)


@login_required
def remove_tag(request, pid):
    podcast = get_object_or_404(Podcast, id=pid)
    tag_str = request.GET.get('tag', '')
    if not tag_str:
        return HttpResponseBadRequest()

    PodcastTag.objects.filter(podcast=podcast, tag=tag_str, source='user', user=request.user).delete()

    if request.GET.get('next', '') == 'mytags':
        return HttpResponseRedirect('/tags/')

    return HttpResponseRedirect('/podcast/%s' % pid)


@manual_gc
@login_required
@allowed_methods(['GET', 'POST'])
def subscribe(request, pid):
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
                podcast.subscribe(device)
            except IntegrityError, e:
                log('error while subscribing to podcast (device %s, podcast %s)' % (device.id, podcast.id))

            return HttpResponseRedirect('/podcast/%s' % podcast.id)

        except ValueError, e:
            error_message = _('Could not subscribe to the podcast: %s' % e)

    targets = podcast.subscribe_targets(request.user)

    form = SyncForm()
    form.set_targets(targets, _('Choose a device:'))

    return render_to_response('subscribe.html', {
        'error_message': error_message,
        'podcast': podcast,
        'can_subscribe': len(targets) > 0,
        'form': form
    }, context_instance=RequestContext(request))


@manual_gc
@login_required
def unsubscribe(request, pid, device_id):

    return_to = request.GET.get('return_to', None)

    if not return_to:
        raise Http404('Wrong URL')

    podcast = get_object_or_404(Podcast, pk=pid)
    device = get_object_or_404(Device, pk=device_id, user=request.user)
    try:
        podcast.unsubscribe(device)
    except IntegrityError, e:
        log('error while unsubscribing from podcast (device %s, podcast %s)' % (device.id, podcast.id))

    return HttpResponseRedirect(return_to)


@manual_gc
@login_required
def subscribe_url(request):
    url = request.GET.get('url', None)

    if not url:
        raise Http404('http://my.gpodder.org/subscribe?url=http://www.example.com/podcast.xml')

    url = sanitize_url(url)

    if url == '':
        raise Http404('Please specify a valid url')

    podcast, created = Podcast.objects.get_or_create(url=url)

    return HttpResponseRedirect('/podcast/%d/subscribe' % podcast.pk)
