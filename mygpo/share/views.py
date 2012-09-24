from functools import wraps

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.template.defaultfilters import slugify
from django.contrib.sites.models import RequestSite
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import cache_control
from django.views.generic.base import View
from django.utils.decorators import method_decorator

from mygpo.core.models import Podcast
from mygpo.core.proxy import proxy_object
from mygpo.api.simple import format_podcast_list
from mygpo.share.models import PodcastList
from mygpo.users.models import User
from mygpo.directory.views import search as directory_search
from mygpo.decorators import repeat_on_conflict
from mygpo.userfeeds.feeds import FavoriteFeed
from mygpo.db.couchdb.podcast import podcasts_by_id, podcast_for_url
from mygpo.db.couchdb.podcastlist import podcastlist_for_user_slug, \
         podcastlists_for_user
from mygpo.data.feeddownloader import PodcastUpdater



def list_decorator(must_own=False):
    def _tmp(f):
        @wraps(f)
        def _decorator(request, username, listname, *args, **kwargs):

            user = User.get_user(username)
            if not user:
                raise Http404

            if must_own and request.user != user:
                return HttpResponseForbidden()

            plist = podcastlist_for_user_slug(user._id, listname)

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

    lists = podcastlists_for_user(request.user._id)

    return render(request, 'lists.html', {
            'lists': lists
        })


def lists_user(request, username):

    user = User.get_user(username)
    if not user:
        raise Http404

    lists = podcastlists_for_user(user._id)

    return render(request, 'lists_user.html', {
            'lists': lists,
            'user': user,
        })


@list_decorator(must_own=False)
def list_show(request, plist, owner):

    is_own = owner == request.user

    plist = proxy_object(plist)

    podcasts = podcasts_by_id(plist.podcasts)
    plist.podcasts = podcasts

    max_subscribers = max([p.subscriber_count() for p in podcasts] + [0])

    site = RequestSite(request)

    return render(request, 'list.html', {
            'podcastlist': plist,
            'max_subscribers': max_subscribers,
            'owner': owner,
            'domain': site.domain,
            'is_own': is_own,
        })


@list_decorator(must_own=False)
def list_opml(request, plist, owner):
    podcasts = podcasts_by_id(plist.podcasts)
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

    plist = podcastlist_for_user_slug(request.user._id, slug)

    if plist is None:
        plist = PodcastList()
        plist.title = title
        plist.slug = slug
        plist.user = request.user._id
        plist.save()

    list_url = reverse('list-show', args=[request.user.username, slug])
    return HttpResponseRedirect(list_url)


@login_required
@list_decorator(must_own=True)
def add_podcast(request, plist, owner, podcast_id):

    plist.podcasts.append(podcast_id)
    plist.save()

    list_url = reverse('list-show', args=[owner.username, plist.slug])
    return HttpResponseRedirect(list_url)


@login_required
@list_decorator(must_own=True)
def remove_podcast(request, plist, owner, podcast_id):
    plist.podcasts.remove(podcast_id)
    plist.save()

    list_url = reverse('list-show', args=[owner.username, plist.slug])
    return HttpResponseRedirect(list_url)


@login_required
@list_decorator(must_own=True)
def delete_list(request, plist, owner):
    plist.delete()
    return HttpResponseRedirect(reverse('lists-overview'))


@login_required
@list_decorator(must_own=False)
def rate_list(request, plist, owner):
    rating_val = int(request.GET.get('rate', None))

    plist.rate(rating_val, request.user._id)
    plist.save()

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
            request.user.favorite_feeds_token = ''
            request.user.save()

        else:
            request.user.create_new_token('favorite_feeds_token', 8)
            request.user.save()

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

        podcast = podcast_for_url(feed_url)

        token = request.user.favorite_feeds_token

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

        self.update(request.user)

        return HttpResponseRedirect(reverse('share'))


    @repeat_on_conflict(['user'])
    def update(self, user):
        if self.public:
            user.subscriptions_token = ''
        else:
            user.create_new_token('subscriptions_token')

        user.save()


class FavoritesFeedCreateEntry(View):
    """ Creates a Podcast object for the user's favorites feed """

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_control(private=True))
    @method_decorator(login_required)
    def post(self, request):
        user = request.user

        feed = favfeed(user)
        site = RequestSite(request)
        feed_url = feed.get_public_url(site.domain)

        podcast = podcast_for_url(feed_url, create=True)

        if not podcast.get_id() in user.published_objects:
            user.published_objects.append(podcast.get_id())
            user.save()

        updater = PodcastUpdater()
        update.update_podcast(podcast)

        return HttpResponseRedirect(reverse('share-favorites'))


@login_required
def overview(request):
    user = request.user
    site = RequestSite(request)

    subscriptions_token = user.get_token('subscriptions_token')
    userpage_token = user.get_token('userpage_token')
    favfeed_token = user.get_token('favorite_feeds_token')

    favfeed = FavoriteFeed(user)
    favfeed_url = favfeed.get_public_url(site.domain)
    favfeed_podcast = podcast_for_url(favfeed_url)

    return render(request, 'share/overview.html', {
        'site': site,
        'subscriptions_token': subscriptions_token,
        'userpage_token': userpage_token,
        'favfeed_token': favfeed_token,
        'favfeed_podcast': favfeed_podcast,
        })


@login_required
def set_token_public(request, token_name, public):

    if public:
        @repeat_on_conflict(['user'])
        def _update(user):
            setattr(user, token_name, '')
            user.save()

    else:
        @repeat_on_conflict(['user'])
        def _update(user):
            user.create_new_token(token_name)
            user.save()

    _update(user=request.user)

    return HttpResponseRedirect(reverse('share'))
