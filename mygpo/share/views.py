from functools import wraps
from datetime import datetime

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from django.contrib.sites.models import RequestSite
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import cache_control
from django.views.generic.base import View
from django.utils.decorators import method_decorator

from mygpo.podcasts.models import Podcast, PodcastGroup
from mygpo.core.proxy import proxy_object
from mygpo.api.simple import format_podcast_list
from mygpo.share.models import PodcastList
from mygpo.directory.views import search as directory_search
from mygpo.decorators import repeat_on_conflict
from mygpo.flattr import Flattr
from mygpo.userfeeds.feeds import FavoriteFeed
from mygpo.db.couchdb.podcastlist import podcastlist_for_user_slug, \
         podcastlists_for_user, add_podcast_to_podcastlist, \
         remove_podcast_from_podcastlist, delete_podcastlist, \
         create_podcast_list
from mygpo.data.feeddownloader import PodcastUpdater

import logging
logger = logging.getLogger(__name__)


def list_decorator(must_own=False):
    def _tmp(f):
        @wraps(f)
        def _decorator(request, username, listname, *args, **kwargs):

            User = get_user_model()
            user = get_object_or_404(User, username=username)

            if must_own and request.user != user:
                return HttpResponseForbidden()

            plist = podcastlist_for_user_slug(user.profile.uuid.hex, listname)

            if plist is None:
                raise Http404

            return f(request, plist, user, *args, **kwargs)

        return _decorator

    return _tmp


@login_required
def search(request, username, listname):
    return directory_search(request, 'list_search.html',
            {'listname': listname})


@login_required
def lists_own(request):

    lists = podcastlists_for_user(request.user.profile.uuid.hex)

    return render(request, 'lists.html', {
            'lists': lists
        })


def lists_user(request, username):

    User = get_user_model()
    user = get_object_or_404(User, username=username)
    lists = podcastlists_for_user(user.profile.uuid.hex)

    return render(request, 'lists_user.html', {
            'lists': lists,
            'user': user,
        })


@list_decorator(must_own=False)
def list_show(request, plist, owner):

    is_own = owner == request.user
    site = RequestSite(request)

    plist = proxy_object(plist)

    podcasts = get_podcasts_groups(plist.podcasts)
    plist.podcasts = podcasts

    max_subscribers = max([p.subscriber_count() for p in podcasts] + [0])

    thing = plist.get_flattr_thing(site.domain, owner.username)
    flattr = Flattr(owner, site.domain, request.is_secure())
    flattr_autosubmit = flattr.get_autosubmit_url(thing)

    return render(request, 'list.html', {
            'podcastlist': plist,
            'max_subscribers': max_subscribers,
            'owner': owner,
            'flattr_autosubmit': flattr_autosubmit,
            'domain': site.domain,
            'is_own': is_own,
        })


@list_decorator(must_own=False)
def list_opml(request, plist, owner):
    podcasts = get_podcasts_groups(plist.podcasts)
    return format_podcast_list(podcasts, 'opml', plist.title)


@login_required
def create_list(request):
    title = request.POST.get('title', None)

    if not title:
        messages.error(request, _('You have to specify a title.'))
        return HttpResponseRedirect(reverse('lists-overview'))

    slug = slugify(title)

    if not slug:
        messages.error(request, _('"{title}" is not a valid title').format(
                    title=title))
        return HttpResponseRedirect(reverse('lists-overview'))

    plist = podcastlist_for_user_slug(request.user.profile.uuid.hex, slug)

    if plist is None:
        create_podcast_list(title, slug, request.user.profile.uuid.hex, datetime.utcnow())

    list_url = reverse('list-show', args=[request.user.username, slug])
    return HttpResponseRedirect(list_url)


@login_required
@list_decorator(must_own=True)
def add_podcast(request, plist, owner, podcast_id):
    add_podcast_to_podcastlist(plist, podcast_id)
    list_url = reverse('list-show', args=[owner.username, plist.slug])
    return HttpResponseRedirect(list_url)


@login_required
@list_decorator(must_own=True)
def remove_podcast(request, plist, owner, podcast_id):
    remove_podcast_from_podcastlist(plist, podcast_id)
    list_url = reverse('list-show', args=[owner.username, plist.slug])
    return HttpResponseRedirect(list_url)


@login_required
@list_decorator(must_own=True)
def delete_list(request, plist, owner):
    delete_podcastlist(plist)
    return HttpResponseRedirect(reverse('lists-overview'))


@login_required
@list_decorator(must_own=False)
def rate_list(request, plist, owner):
    rating_val = int(request.GET.get('rate', None))

    @repeat_on_conflict(['plist'])
    def _rate(plist, rating_val, user):
        plist.rate(rating_val, user.profile.uuid.hex)
        plist.save()

    _rate(plist, rating_val, request.user)

    messages.success(request, _('Thanks for rating!'))

    list_url = reverse('list-show', args=[owner.username, plist.slug])
    return HttpResponseRedirect(list_url)


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
            request.user.profile.create_new_token('favorite_feeds_token', 8)
            request.user.profile.save()

        token = request.user.favorite_feeds_token

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

        if not podcast.get_id() in user.published_objects:
            user.published_objects.append(podcast.get_id())
            user.save()

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


def get_podcasts_groups(ids):
    # this could be optimized by using a View
    logger.info('Getting podcasts and groups for IDs %r', ids)
    groups = PodcastGroup.objects.filter(id__in=ids)
    podcasts = Podcast.objects.filter(id__in=ids)
    # TODO: bring in right order, according to IDs
    return list(groups) + list(podcasts)
