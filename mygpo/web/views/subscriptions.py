from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from mygpo.utils import parse_bool
from mygpo.decorators import requires_token
from mygpo.api.models import Device, Subscription, Episode
from mygpo.api import backend, simple
from mygpo.web.models import SecurityToken
from mygpo.web import utils


@login_required
def list(request):
    current_site = Site.objects.get_current()
    subscriptionlist = create_subscriptionlist(request)
    return render_to_response('subscriptions.html', {
        'subscriptionlist': subscriptionlist,
        'url': current_site
    }, context_instance=RequestContext(request))


@login_required
def download_all(request):
    podcasts = backend.get_all_subscriptions(request.user)
    response = simple.format_podcast_list(podcasts, 'opml', request.user.username)
    response['Content-Disposition'] = 'attachment; filename=all-subscriptions.opml'
    return response


@requires_token(object='subscriptions', action='r', denied_template='user_subscriptions_denied.html')
def for_user(request, username):
    user = get_object_or_404(User, username=username)
    subscriptions = Subscription.objects.public_subscribed_podcasts(user)
    token = SecurityToken.objects.get(object='subscriptions', action='r', user__username=username)

    return render_to_response('user_subscriptions.html', {
        'subscriptions': subscriptions,
        'other_user': user,
        'token': token,
        }, context_instance=RequestContext(request))

@requires_token(object='subscriptions', action='r')
def for_user_opml(request, username):
    user = get_object_or_404(User, username=username)
    subscriptions = Subscription.objects.public_subscribed_podcasts(user)

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

