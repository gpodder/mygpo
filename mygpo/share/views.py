from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
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



class ShareFavorites(View):

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_control(private=True))
    @method_decorator(login_required)
    def get(self, request):
        user = request.user

        favfeed = FavoriteFeed(user)
        site = RequestSite(request)
        feed_url = favfeed.get_public_url(site.domain)

        podcast = Podcast.objects.filter(urls__url=feed_url).first()

        token = user.profile.favorite_feeds_token

        return render(request, 'share/favorites.html', {
            'feed_token': token,
            'site': site,
            'podcast': podcast,
            })


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
def overview(request):
    user = request.user
    site = RequestSite(request)

    subscriptions_token = user.profile.get_token('subscriptions_token')
    userpage_token = user.profile.get_token('userpage_token')
    favfeed_token = user.profile.get_token('favorite_feeds_token')

    favfeed = FavoriteFeed(user)
    favfeed_url = favfeed.get_public_url(site.domain)
    favfeed_podcast = Podcast.objects.filter(urls__url=favfeed_url).first()

    return render(request, 'share/overview.html', {
        'site': site,
        'subscriptions_token': subscriptions_token,
        'userpage_token': userpage_token,
        'favfeed_token': favfeed_token,
        'favfeed_podcast': favfeed_podcast,
        })


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
