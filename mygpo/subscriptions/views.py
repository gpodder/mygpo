from datetime import datetime

from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.sites.requests import RequestSite
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import cache_control
from django.utils.translation import gettext as _
from django.contrib.syndication.views import Feed
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast
from mygpo.subscriptions.models import Subscription
from mygpo.users.settings import PUBLIC_SUB_PODCAST
from mygpo.api import simple
from mygpo.subscriptions import get_subscribed_podcasts
from mygpo.decorators import requires_token
from mygpo.users.models import HistoryEntry
from mygpo.subscriptions import (
    get_subscribed_podcasts,
    get_subscription_change_history,
    get_subscription_history,
)
from mygpo.web.utils import get_podcast_link_target
from mygpo.utils import parse_bool
from mygpo.decorators import requires_token
from mygpo.web.utils import symbian_opml_changes


@vary_on_cookie
@cache_control(private=True)
@login_required
def show_list(request):
    current_site = RequestSite(request)
    subscriptionlist = create_subscriptionlist(request)
    return render(
        request,
        "subscriptions.html",
        {
            "subscriptionlist": subscriptionlist,
            "url": current_site,
            "podcast_ad": Podcast.objects.get_advertised_podcast(),
        },
    )


@vary_on_cookie
@cache_control(private=True)
@login_required
def download_all(request):
    podcasts = get_subscribed_podcasts(request.user)
    response = simple.format_podcast_list(podcasts, "opml", request.user.username)
    response["Content-Disposition"] = "attachment; filename=all-subscriptions.opml"
    return response


def create_subscriptionlist(request):
    user = request.user

    # get all non-deleted subscriptions
    subscriptions = (
        Subscription.objects.filter(user=user)
        .exclude(deleted=True)
        .select_related("podcast", "client")
        .prefetch_related("podcast__slugs")
    )

    # grou clients by subscribed podcasts
    subscription_list = {}
    for subscription in subscriptions:
        podcast = subscription.podcast

        if not podcast in subscription_list:
            subscription_list[podcast] = {
                "podcast": podcast,
                "devices": [],
                "episodes": podcast.episode_count,
            }

        subscription_list[podcast]["devices"].append(subscription.client)

    # sort most recently updated podcast first
    subscriptions = subscription_list.values()
    now = datetime.utcnow()
    sort_key = lambda s: s["podcast"].latest_episode_timestamp or now
    subscriptions = sorted(subscriptions, key=sort_key, reverse=True)
    return subscriptions


@requires_token(token_name="subscriptions_token")
def subscriptions_feed(request, username):
    # Create to feed manually so we can wrap the token-authentication around it
    f = SubscriptionsFeed(username)
    obj = f.get_object(request, username)
    feedgen = f.get_feed(obj, request)
    response = HttpResponse(content_type=feedgen.content_type)
    feedgen.write(response, "utf-8")
    return response


class SubscriptionsFeed(Feed):
    """A feed showing subscription changes for a certain user"""

    NUM_ITEMS = 20

    def __init__(self, username):
        self.username = username

    def get_object(self, request, username):
        self.site = RequestSite(request)
        User = get_user_model()
        user = get_object_or_404(User, username=username)
        return user

    def title(self, user):
        return _("%(username)s's Podcast Subscriptions on %(site)s") % dict(
            username=user.username, site=self.site
        )

    def description(self, user):
        return _(
            "Recent changes to %(username)s's podcast subscriptions on %(site)s"
        ) % dict(username=user.username, site=self.site)

    def link(self, user):
        return reverse("shared-subscriptions", args=[user.username])

    def items(self, user):
        history = get_subscription_history(user, public_only=True)
        history = get_subscription_change_history(history)
        history = list(history)[-self.NUM_ITEMS :]
        return history

    def author_name(self, user):
        return user.username

    def author_link(self, user):
        return reverse("shared-subscriptions", args=[user.username])

    # entry-specific data below

    description_template = "subscription-feed-description.html"

    def item_title(self, entry):
        if entry.action == "subscribe":
            s = _("%(username)s subscribed to %(podcast)s (%(site)s)")
        else:
            s = _("%(username)s unsubscribed from %(podcast)s (%(site)s)")

        return s % dict(
            username=self.username, podcast=entry.podcast.display_title, site=self.site
        )

    def item_link(self, item):
        return get_podcast_link_target(item.podcast)

    def item_pubdate(self, item):
        return item.timestamp


@requires_token(
    token_name="subscriptions_token", denied_template="user_subscriptions_denied.html"
)
def for_user(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    subscriptions = get_subscribed_podcasts(user, only_public=True)
    token = user.profile.get_token("subscriptions_token")

    return render(
        request,
        "user_subscriptions.html",
        {"subscriptions": subscriptions, "other_user": user, "token": token},
    )


@requires_token(token_name="subscriptions_token")
def for_user_opml(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    subscriptions = get_subscribed_podcasts(user, only_public=True)

    if parse_bool(request.GET.get("symbian", False)):
        subscriptions = map(symbian_opml_changes, [p.podcast for p in subscriptions])

    response = render(
        request,
        "user_subscriptions.opml",
        {"subscriptions": subscriptions, "other_user": user},
    )
    response["Content-Disposition"] = (
        "attachment; filename=%s-subscriptions.opml" % username
    )
    return response
