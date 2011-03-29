from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.models import RequestSite
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.syndication.views import Feed
from django.utils.translation import ugettext as _
from django.http import HttpResponse

from mygpo.core.models import Podcast
from mygpo.utils import parse_bool, unzip, get_to_dict, skip_pairs
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
    # only loaded once, not for each occurance in a subscription
    public, podcast_ids, device_ids = unzip(subscriptions)
    podcast_ids= list(set(podcast_ids))
    device_ids = list(set(device_ids))

    podcasts = get_to_dict(Podcast, podcast_ids)
    devices = dict([ (id, user.get_device(id)) for id in device_ids])

    subscription_list = {}
    for public, podcast_id, device_id in subscriptions:
        device = devices[device_id]
        if not podcast_id in subscription_list:
            podcast = podcasts[podcast_id]
            e = Episode.objects.filter(podcast=podcast.get_old_obj(), timestamp__isnull=False).order_by('-timestamp')
            episode = e[0] if e.count() > 0 else None
            subscription_list[podcast_id] = {'podcast': podcasts[podcast_id], 'devices': [device], 'episode': episode}
        else:
            subscription_list[podcast_id]['devices'].append(device)

    return subscription_list.values()


@requires_token(token_name='subscriptions_token')
def subscriptions_feed(request, username):
    # Create to feed manually so we can wrap the token-authentication around it
    f = SubscriptionsFeed()
    obj = f.get_object(request, username)
    feedgen = f.get_feed(obj, request)
    response = HttpResponse(mimetype=feedgen.mime_type)
    feedgen.write(response, 'utf-8')
    return response


class SubscriptionsFeed(Feed):
    """ A feed showing subscription changes for a certain user """

    def get_object(self, request, username):
        self.site = RequestSite(request)
        user = User.objects.get(username=username)
        return migrate.get_or_migrate_user(user)

    def title(self, user):
        return _('%(username)s\'s Subscriptions') % dict(username=user.username)

    def description(self, user):
        return _('Recent changes to %(username)s\'s podcast subscriptions on %(site)s') % \
            dict(username=user.username, site=self.site)

    def link(self, user):
        return reverse('shared-subscriptions', args=[user.username])

    def items(self, user):
        NUM_ITEMS = 20
        history = user.get_global_subscription_history(public=True)
        history = skip_pairs(history)
        history = list(history)[-NUM_ITEMS:]

        # load podcast and device data
        podcast_ids = [x.podcast_id for x in history]
        podcasts = get_to_dict(Podcast, podcast_ids)

        device_ids = [x.device_id for x in history]
        devices = dict([ (id, user.get_device(id)) for id in device_ids])

        for entry in history:
            entry.podcast = podcasts[entry.podcast_id]
            entry.device = devices[entry.device_id]
            entry.user = user

        return history

    def author_name(self, user):
        return user.username

    def author_link(self, user):
        return reverse('shared-subscriptions', args=[user.username])

    # entry-specific data below

    description_template = "subscription-feed-description.html"

    def item_title(self, entry):
        if entry.action == 'subscribe':
            s = _('%(username)s subscribed to %(podcast)s')
        else:
            s = _('%(username)s unsubscribed from %(podcast)s')

        return s % dict(username=entry.user.username,
                        podcast=entry.podcast.display_title)

    def item_link(self, item):
        return reverse('podcast', args=[item.podcast.oldid])

    def item_pubdate(self, item):
        return item.timestamp
