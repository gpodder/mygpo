from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.models import RequestSite
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from mygpo.core.models import Podcast
from mygpo.utils import parse_bool, unzip
from mygpo.decorators import manual_gc, requires_token
from mygpo.api.models import Device, Episode
from mygpo.api import backend, simple
from mygpo.web import utils
from mygpo import migrate


@manual_gc
@login_required
def show_list(request):
    current_site = RequestSite(request)
    subscriptionlist = create_subscriptionlist(request)
    return render_to_response('subscriptions.html', {
        'subscriptionlist': subscriptionlist,
        'url': current_site
    }, context_instance=RequestContext(request))


@manual_gc
@login_required
def download_all(request):
    user = migrate.get_or_migrate_user(request.user)
    podcasts = user.get_subscribed_podcasts()
    response = simple.format_podcast_list(podcasts, 'opml', request.user.username)
    response['Content-Disposition'] = 'attachment; filename=all-subscriptions.opml'
    return response


@manual_gc
@requires_token(token_name='subscriptions_token', denied_template='user_subscriptions_denied.html')
def for_user(request, username):
    user = get_object_or_404(User, username=username)
    new_user = migrate.get_or_migrate_user(user)

    subscriptions = new_user.get_subscribed_podcasts(public=True)
    token = new_user.subscriptions_token

    return render_to_response('user_subscriptions.html', {
        'subscriptions': subscriptions,
        'other_user': user,
        'token': token,
        }, context_instance=RequestContext(request))

@requires_token(token_name='subscriptions_token')
def for_user_opml(request, username):
    user = get_object_or_404(User, username=username)
    new_user = migrate.get_or_migrate_user(user)
    subscriptions = new_user.get_subscribed_podcasts(public=True)

    if parse_bool(request.GET.get('symbian', False)):
        subscriptions = map(utils.symbian_opml_changes, subscriptions)

    response = render_to_response('user_subscriptions.opml', {
        'subscriptions': subscriptions,
        'other_user': user
        }, context_instance=RequestContext(request))
    response['Content-Disposition'] = 'attachment; filename=%s-subscriptions.opml' % username
    return response


def create_subscriptionlist(request):
    #sync all devices first
    for d in Device.objects.filter(user=request.user):
        d.sync()

    user = migrate.get_or_migrate_user(request.user)
    subscriptions = user.get_subscriptions()

    if not subscriptions:
        return []

    # Load all Podcasts and Devices first to ensure that they are
    # only loaded once, not for each occurance in a Subscription
    podcast_ids, device_ids = unzip(subscriptions)
    podcast_ids= list(set(podcast_ids))
    device_ids = list(set(device_ids))

    pobj = Podcast.get_multi(podcast_ids)
    podcasts = dict(zip(podcast_ids, pobj))
    devices = dict([ (id, user.get_device(id)) for id in device_ids])

    subscription_list = {}
    for podcast_id, device_id in subscriptions:
        device = devices[device_id]
        if not podcast_id in subscription_list:
            podcast = podcasts[podcast_id]
            e = Episode.objects.filter(podcast=podcast.get_old_obj(), timestamp__isnull=False).order_by('-timestamp')
            episode = e[0] if e.count() > 0 else None
            subscription_list[podcast_id] = {'podcast': podcasts[podcast_id], 'devices': [device], 'episode': episode}
        else:
            subscription_list[podcast_id]['devices'].append(device)

    return subscription_list.values()
