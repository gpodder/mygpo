from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.sites.models import RequestSite
from django.contrib.auth.decorators import login_required
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import cache_control
from django.views.generic.base import View
from django.utils.decorators import method_decorator

from mygpo.podcasts.models import Podcast
from mygpo.publisher.models import PublishedPodcast
from mygpo.userfeeds.feeds import FavoriteFeed
from mygpo.data.feeddownloader import PodcastUpdater

import logging
logger = logging.getLogger(__name__)


class FavoritesPublic(View):

    public = True

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_control(private=True))
    @method_decorator(login_required)
    def post(self, request):

        if self.public:
            request.user.profile.favorite_feeds_token = ''
            request.user.profile.save()

        else:
            request.user.profile.create_new_token('favorite_feeds_token')
            request.user.profile.save()

        return HttpResponseRedirect(reverse('share-favorites'))


class PublicSubscriptions(View):

    public = True

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_control(private=True))
    @method_decorator(login_required)
    def post(self, request):

        if self.public:
            user.profile.subscriptions_token = ''
        else:
            user.profile.create_new_token('subscriptions_token')

        user.profile.save()

        return HttpResponseRedirect(reverse('share'))


class FavoritesFeedCreateEntry(View):
    """ Creates a Podcast object for the user's favorites feed """

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_control(private=True))
    @method_decorator(login_required)
    def post(self, request):
        user = request.user

        feed = FavoriteFeed(user)
        site = RequestSite(request)
        feed_url = feed.get_public_url(site.domain)

        podcast = Podcast.objects.get_or_create_for_url(feed_url)

        PublishedPodcast.objects.get_or_create(
            podcast=podcast,
            publisher=user,
        )

        updater = PodcastUpdater()
        updater.update(feed_url)

        return HttpResponseRedirect(reverse('share-favorites'))


@login_required
def set_token_public(request, token_name, public):

    user = request.user

    if public:
        setattr(user.profile, token_name, '')
        user.profile.save()

    else:
        user.profile.create_new_token(token_name)
        user.profile.save()

    return HttpResponseRedirect(reverse('share'))
