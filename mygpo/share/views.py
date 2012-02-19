from functools import wraps

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.contrib.sites.models import RequestSite
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _

from mygpo.core.models import Podcast
from mygpo.core.proxy import proxy_object
from mygpo.api.simple import format_podcast_list
from mygpo.share.models import PodcastList
from mygpo.users.models import User
from mygpo.directory.views import search as directory_search
from mygpo.decorators import repeat_on_conflict


def list_decorator(must_own=False):
    def _tmp(f):
        @wraps(f)
        def _decorator(request, username, listname, *args, **kwargs):

            user = User.get_user(username)
            if not user:
                raise Http404

            if must_own and request.user != user:
                return HttpResponseForbidden()

            plist = PodcastList.for_user_slug(user._id, listname)

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

    lists = PodcastList.for_user(request.user._id)

    return render_to_response('lists.html', {
            'lists': lists
        }, context_instance=RequestContext(request))


def lists_user(request, username):

    user = User.get_user(username)
    if not user:
        raise Http404

    lists = PodcastList.for_user(user._id)

    return render_to_response('lists_user.html', {
            'lists': lists,
            'user': user,
        }, context_instance=RequestContext(request))


@list_decorator(must_own=False)
def list_show(request, plist, owner):

    is_own = owner == request.user

    plist = proxy_object(plist)

    podcasts = list(Podcast.get_multi(plist.podcasts))
    plist.podcasts = podcasts

    max_subscribers = max([p.subscriber_count() for p in podcasts] + [0])

    site = RequestSite(request)

    return render_to_response('list.html', {
            'podcastlist': plist,
            'max_subscribers': max_subscribers,
            'owner': owner,
            'domain': site.domain,
            'is_own': is_own,
        }, context_instance=RequestContext(request))


@list_decorator(must_own=False)
def list_opml(request, plist, owner):
    podcasts = list(Podcast.get_multi(plist.podcasts))
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

    plist = PodcastList.for_user_slug(request.user._id, slug)

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


@login_required
def overview(request):
    site = RequestSite(request)

    subscriptions_token = request.user.subscriptions_token
    userpage_token = request.user.userpage_token
    favfeed_token = request.user.favorite_feeds_token

    favfeed_url = 'http://%s/%s' % (site.domain, reverse('favorites-feed', args=[request.user.username]))
    favfeed_podcast = Podcast.for_url(favfeed_url)

    return render_to_response('share/overview.html', {
        'site': site,
        'subscriptions_token': subscriptions_token,
        'userpage_token': userpage_token,
        'favfeed_token': favfeed_token,
        'favfeed_podcast': favfeed_podcast,
        }, context_instance=RequestContext(request))


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
