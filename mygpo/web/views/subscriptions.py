from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from django.shortcuts import render
from django.contrib.syndication.views import Feed
from django.utils.translation import ugettext as _
from django.http import HttpResponse, Http404
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control

from mygpo.core.models import Podcast
from mygpo.utils import parse_bool, unzip, skip_pairs
from mygpo.decorators import requires_token
from mygpo.api import backend, simple
from mygpo.users.models import HistoryEntry, User
from mygpo.web import utils
from mygpo.db.couchdb.podcast import podcasts_to_dict


@vary_on_cookie
@cache_control(private=True)
@login_required
def show_list(request):
    current_site = RequestSite(request)
    subscriptionlist = create_subscriptionlist(request)
    return render(request, 'subscriptions.html', {
        'subscriptionlist': subscriptionlist,
        'url': current_site
    })


@vary_on_cookie
@cache_control(private=True)
@login_required
def download_all(request):
    podcasts = request.user.get_subscribed_podcasts()
    response = simple.format_podcast_list(podcasts, 'opml', request.user.username)
    response['Content-Disposition'] = 'attachment; filename=all-subscriptions.opml'
    return response


@requires_token(token_name='subscriptions_token', denied_template='user_subscriptions_denied.html')
def for_user(request, username):
    user = User.get_user(username)
    if not user:
        raise Http404

    subscriptions = user.get_subscribed_podcasts(public=True)
    token = user.get_token('subscriptions_token')

    return render(request, 'user_subscriptions.html', {
        'subscriptions': subscriptions,
        'other_user': user,
        'token': token,
        })

@requires_token(token_name='subscriptions_token')
def for_user_opml(request, username):
    user = User.get_user(username)
    if not user:
        raise Http404

    subscriptions = user.get_subscribed_podcasts(public=True)

    if parse_bool(request.GET.get('symbian', False)):
        subscriptions = map(utils.symbian_opml_changes, subscriptions)

    response = render(request, 'user_subscriptions.opml', {
        'subscriptions': subscriptions,
        'other_user': user
        })
    response['Content-Disposition'] = 'attachment; filename=%s-subscriptions.opml' % username
    return response


def create_subscriptionlist(request):
    user = request.user
    user.sync_all()

    subscriptions = user.get_subscriptions()

    if not subscriptions:
        return []

    # Load all Podcasts and Devices first to ensure that they are
    # only loaded once, not for each occurance in a subscription
    public, podcast_ids, device_ids = unzip(subscriptions)
    podcast_ids= list(set(podcast_ids))
    device_ids = list(set(device_ids))

    podcasts = podcasts_to_dict(podcast_ids)
    devices = dict([ (id, user.get_device(id)) for id in device_ids])

    subscription_list = {}
    for public, podcast_id, device_id in subscriptions:
        device = devices[device_id]
        if not podcast_id in subscription_list:
            podcast = podcasts.get(podcast_id, None)
            if podcast is None:
                continue

            episode = podcast.get_latest_episode()

            subscription_list[podcast_id] = {
                'podcast': podcasts[podcast_id],
                'devices': [device] if device else [],
                'episode': episode
            }
        else:
            if device:
                subscription_list[podcast_id]['devices'].append(device)

    return subscription_list.values()


@requires_token(token_name='subscriptions_token')
def subscriptions_feed(request, username):
    # Create to feed manually so we can wrap the token-authentication around it
    f = SubscriptionsFeed(username)
    obj = f.get_object(request, username)
    feedgen = f.get_feed(obj, request)
    response = HttpResponse(mimetype=feedgen.mime_type)
    feedgen.write(response, 'utf-8')
    return response


class SubscriptionsFeed(Feed):
    """ A feed showing subscription changes for a certain user """

    def __init__(self, username):
        self.username = username

    def get_object(self, request, username):
        self.site = RequestSite(request)
        return User.get_user(username)

    def title(self, user):
        return _('%(username)s\'s Podcast Subscriptions on %(site)s') % \
            dict(username=user.username, site=self.site)

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
        history = HistoryEntry.fetch_data(user, history)
        history = filter(lambda e:e.podcast, history)
        return history

    def author_name(self, user):
        return user.username

    def author_link(self, user):
        return reverse('shared-subscriptions', args=[user.username])

    # entry-specific data below

    description_template = "subscription-feed-description.html"

    def item_title(self, entry):
        if entry.action == 'subscribe':
            s = _('%(username)s subscribed to %(podcast)s (%(site)s)')
        else:
            s = _('%(username)s unsubscribed from %(podcast)s (%(site)s)')

        return s % dict(username=self.username,
                        podcast=entry.podcast.display_title,
                        site=self.site)

    def item_link(self, item):
        return utils.get_podcast_link_target(item.podcast)

    def item_pubdate(self, item):
        return item.timestamp
