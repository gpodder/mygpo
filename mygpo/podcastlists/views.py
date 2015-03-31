import uuid
from functools import wraps
from datetime import datetime

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.contrib.sites.models import RequestSite
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_cookie
from django.utils.translation import ugettext as _
from django.views.generic.base import View

from mygpo.podcasts.models import Podcast, PodcastGroup
from mygpo.podcastlists.models import PodcastList, PodcastListEntry
from mygpo.api.simple import format_podcast_list
from mygpo.votes.models import Vote
from mygpo.flattr import Flattr
from mygpo.api import APIView

import logging
logger = logging.getLogger(__name__)


def list_decorator(must_own=False):
    def _tmp(f):
        @wraps(f)
        def _decorator(request, username, slug, *args, **kwargs):

            User = get_user_model()
            user = get_object_or_404(User, username=username)

            if must_own and request.user != user:
                return HttpResponseForbidden()

            plist = get_object_or_404(PodcastList, user=user, slug=slug)

            return f(request, plist, user, *args, **kwargs)

        return _decorator

    return _tmp


class PodcastListsOfUser(APIView):

    def get(self, request, username):
        User = get_user_model()
        user = get_object_or_404(User, username=username)
        lists = PodcastList.objects.filter(user=user)
        return {
            'user': user,
            'podcastlists': lists,
        }


class PodcastListDetails(APIView):
    @list_decorator(must_own=False)
    def get(self, request, username):

        is_own = owner == request.user

        objs = [entry.content_object for entry in plist.entries.all()]
        max_subscribers = max([p.subscriber_count() for p in objs] + [0])

        thing = plist.get_flattr_thing(site.domain, owner.username)
        flattr = Flattr(owner, site.domain, request.is_secure())
        flattr_autosubmit = flattr.get_autosubmit_url(thing)

        return {
            'podcastlist': plist,
            'owner': owner,
            'flattr_autosubmit': flattr_autosubmit,
            'is_own': is_own,
        }


@list_decorator(must_own=False)
def list_opml(request, plist, owner):
    podcasts = [entry.content_object for entry in plist.entries.all()]
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

    plist, created = PodcastList.objects.get_or_create(
        user=request.user,
        slug=slug,
        defaults={
            'id': uuid.uuid1(),
            'title': title,
        }
    )

    list_url = reverse('list-show', args=[request.user.username, slug])
    return HttpResponseRedirect(list_url)


@login_required
@list_decorator(must_own=True)
def add_podcast(request, plist, owner, podcast_id):

    try:
        obj = Podcast.objects.all().get_by_any_id(podcast_id)
    except Podcast.DoesNotExist:
        try:
            obj = PodcastGroup.objects.get(id=podcast_id)
        except PodcastList.DoesNotExist:
            raise Http404

    plist.add_entry(obj)
    list_url = reverse('list-show', args=[owner.username, plist.slug])
    return HttpResponseRedirect(list_url)


@login_required
@list_decorator(must_own=True)
def remove_podcast(request, plist, owner, order):
    PodcastListEntry.objects.filter(podcastlist=plist, order=order).delete()
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
    now = datetime.utcnow()

    vote, created = Vote.objects.get_or_create(
        user=request.user,
        content_type=ContentType.objects.get_for_model(plist),
        object_id=plist.id,
    )
    messages.success(request, _('Thanks for rating!'))

    list_url = reverse('list-show', args=[owner.username, plist.slug])
    return HttpResponseRedirect(list_url)


class RandomPodcastList(APIView):

    def get(self, request, podcasts_per_list=5):
        random_list = PodcastList.objects.order_by('?').first()
        yield random_list


class PodcastListsOverview(APIView):

    @cache_control(private=True)
    @vary_on_cookie
    def get(self, request, page_size=20):

        lists = PodcastList.objects.all()\
                                   .annotate(num_votes=Count('votes'))\
                                   .order_by('-num_votes')

        paginator = Paginator(lists, page_size)

        page = request.GET.get('page')
        try:
            lists = paginator.page(page)
        except PageNotAnInteger:
            lists = paginator.page(1)
            page = 1
        except EmptyPage:
            lists = paginator.page(paginator.num_pages)
            page = paginator.num_pages

        num_pages = int(ceil(PodcastList.objects.count() / float(page_size)))
        page_list = get_page_list(1, num_pages, int(page), 15)

        return {
            'lists': lists,
            'page_list': page_list,
        }
