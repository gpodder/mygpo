from functools import wraps, partial
from datetime import datetime

from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.sites.requests import RequestSite
from django.utils.translation import gettext as _
from django.contrib import messages
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

from mygpo.podcasts.models import Podcast, PodcastGroup, Episode, Tag
from mygpo.users.models import SubscriptionException
from mygpo.subscriptions.models import Subscription
from mygpo.subscriptions import (
    subscribe as subscribe_podcast,
    unsubscribe as unsubscribe_podcast,
    subscribe_all as subscribe_podcast_all,
    unsubscribe_all as unsubscribe_podcast_all,
    get_subscribe_targets,
)
from mygpo.history.models import HistoryEntry
from mygpo.utils import normalize_feed_url, to_maxlength
from mygpo.users.settings import PUBLIC_SUB_PODCAST
from mygpo.publisher.utils import check_publisher_permission
from mygpo.usersettings.models import UserSettings
from mygpo.users.models import Client
from mygpo.web.forms import SyncForm
from mygpo.decorators import allowed_methods
from mygpo.web.utils import get_podcast_link_target, get_page_list, check_restrictions

import logging

logger = logging.getLogger(__name__)


@vary_on_cookie
@cache_control(private=True)
@allowed_methods(['GET'])
def show(request, podcast):
    """ Shows a podcast detail page """

    podcast = check_restrictions(podcast)

    current_site = RequestSite(request)
    num_episodes = 20
    episodes = episode_list(podcast, request.user, limit=num_episodes)
    user = request.user

    # TODO: move into EpisodeList (?) class
    listeners = [e.listeners for e in episodes if e.listeners is not None]
    max_listeners = max(listeners, default=0)

    episode = None

    if episodes:
        episode = episodes[0]
        episodes = episodes[1:]

    if podcast.group:
        group = podcast.group
        rel_podcasts = group.podcast_set.all()
    else:
        rel_podcasts = []

    tags = get_tags(podcast, user)
    has_tagged = any(t['is_own'] for t in tags)

    if user.is_authenticated:
        subscribed_devices = Client.objects.filter(
            subscription__user=user, subscription__podcast=podcast
        )

        subscribe_targets = get_subscribe_targets(podcast, user)

        has_history = HistoryEntry.objects.filter(user=user, podcast=podcast).exists()

    else:
        has_history = False
        subscribed_devices = []
        subscribe_targets = []

    is_publisher = check_publisher_permission(user, podcast)

    episodes_total = podcast.episode_count or 0
    num_pages = episodes_total / num_episodes
    page_list = get_page_list(1, num_pages, 1, 15)

    return render(
        request,
        'podcast.html',
        {
            'tags': tags,
            'has_tagged': has_tagged,
            'url': current_site,
            'has_history': has_history,
            'podcast': podcast,
            'devices': subscribed_devices,
            'related_podcasts': rel_podcasts,
            'can_subscribe': len(subscribe_targets) > 0,
            'subscribe_targets': subscribe_targets,
            'episode': episode,
            'episodes': episodes,
            'max_listeners': max_listeners,
            'is_publisher': is_publisher,
            'page_list': page_list,
            'current_page': 1,
        },
    )


def get_tags(podcast, user, max_tags=50):
    """ Returns all tags that user sees for the given podcast

    The tag list is a list of dicts in the form of {'tag': 'tech', 'is_own':
    True}. "is_own" indicates if the tag was created by the given user. """
    tags = {}

    for tag in podcast.tags.all():
        t = tag.tag.lower()
        if not t in tags:
            tags[t] = {'tag': t, 'is_own': False}

        if tag.user == user:
            tags[t]['is_own'] = True

    return list(tags.values())


def episode_list(podcast, user, offset=0, limit=20):
    """ Returns a list of episodes """
    # fast pagination by using Episode.order instead of offset/limit
    if podcast.max_episode_order is None:
        return []

    page_start = podcast.max_episode_order - offset
    page_end = page_start - limit
    return (
        Episode.objects.filter(
            podcast=podcast, order__lte=page_start, order__gt=page_end
        )
        .prefetch_related('slugs')
        .order_by('-order')
    )


def all_episodes(request, podcast, page_size=20):

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    user = request.user

    episodes = episode_list(podcast, user, (page - 1) * page_size, page_size)
    episodes_total = podcast.episode_count or 0
    num_pages = episodes_total / page_size
    page_list = get_page_list(1, num_pages, page, 15)

    listeners = [e.listeners for e in episodes if e.listeners is not None]
    max_listeners = max(listeners, default=0)

    is_publisher = check_publisher_permission(user, podcast)

    return render(
        request,
        'episodes.html',
        {
            'podcast': podcast,
            'episodes': episodes,
            'max_listeners': max_listeners,
            'page_list': page_list,
            'current_page': page,
            'is_publisher': is_publisher,
        },
    )


@never_cache
@login_required
def add_tag(request, podcast):

    tag_str = request.GET.get('tag', '')
    if not tag_str:
        return HttpResponseBadRequest()

    user = request.user

    tags = tag_str.split(',')
    tags = map(str.strip, tags)
    tags = map(str.lower, tags)
    tags = list(filter(None, tags))

    ContentType.objects.get_for_model(podcast)

    for tag in tags:

        # trim to maximum length
        tag = to_maxlength(Tag, 'tag', tag)

        Tag.objects.get_or_create(
            tag=tag,
            source=Tag.USER,
            user=user,
            content_type=ContentType.objects.get_for_model(podcast),
            object_id=podcast.id,
        )

    if request.GET.get('next', '') == 'mytags':
        return HttpResponseRedirect('/tags/')

    return HttpResponseRedirect(get_podcast_link_target(podcast))


@never_cache
@login_required
def remove_tag(request, podcast):

    tag_str = request.GET.get('tag', None)
    if tag_str is None:
        return HttpResponseBadRequest()

    user = request.user

    tags = tag_str.split(',')
    tags = list(map(str.strip, tags))

    ContentType.objects.get_for_model(podcast)

    for tag in tags:
        Tag.objects.filter(
            tag__iexact=tag,
            source=Tag.USER,
            user=user,
            content_type=ContentType.objects.get_for_model(podcast),
            object_id=podcast.id,
        ).delete()

    if request.GET.get('next', '') == 'mytags':
        return HttpResponseRedirect('/tags/')

    return HttpResponseRedirect(get_podcast_link_target(podcast))


@never_cache
@login_required
@allowed_methods(['GET', 'POST'])
def subscribe(request, podcast):

    if request.method == 'POST':

        # multiple UIDs from the /podcast/<slug>/subscribe
        device_uids = [k for (k, v) in request.POST.items() if k == v]

        # single UID from /podcast/<slug>
        if 'targets' in request.POST:
            devices = request.POST.get('targets')
            devices = devices.split(',')
            device_uids.extend(devices)

        for uid in device_uids:
            try:
                device = request.user.client_set.get(uid=uid)
                subscribe_podcast(podcast, request.user, device)

            except Client.DoesNotExist as e:
                messages.error(request, str(e))

        return HttpResponseRedirect(get_podcast_link_target(podcast))

    targets = get_subscribe_targets(podcast, request.user)

    return render(request, 'subscribe.html', {'targets': targets, 'podcast': podcast})


@never_cache
@login_required
@allowed_methods(['POST'])
def subscribe_all(request, podcast):
    """ subscribe all of the user's devices to the podcast """
    user = request.user
    subscribe_podcast_all(podcast, user)
    return HttpResponseRedirect(get_podcast_link_target(podcast))


@never_cache
@login_required
def unsubscribe(request, podcast, device_uid):

    return_to = request.GET.get('return_to', None)

    if not return_to:
        raise Http404('Wrong URL')

    user = request.user
    try:
        device = user.client_set.get(uid=device_uid)

    except Client.DoesNotExist as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(return_to)

    try:
        unsubscribe_podcast(podcast, user, device)
    except SubscriptionException as e:
        logger.exception(
            'Web: %(username)s: could not unsubscribe from podcast %(podcast_url)s on device %(device_id)s'
            % {
                'username': request.user.username,
                'podcast_url': podcast.url,
                'device_id': device.id,
            }
        )

    return HttpResponseRedirect(return_to)


@never_cache
@login_required
@allowed_methods(['POST'])
def unsubscribe_all(request, podcast):
    """ unsubscribe all of the user's devices from the podcast """
    user = request.user
    unsubscribe_podcast_all(podcast, user)
    return HttpResponseRedirect(get_podcast_link_target(podcast))


@never_cache
@login_required
def subscribe_url(request):
    url = request.GET.get('url', None)

    if not url:
        raise Http404(
            'http://my.gpodder.org/subscribe?url=http://www.example.com/podcast.xml'
        )

    url = normalize_feed_url(url)

    if not url:
        raise Http404('Please specify a valid url')

    podcast = Podcast.objects.get_or_create_for_url(url).object

    return HttpResponseRedirect(get_podcast_link_target(podcast, 'subscribe'))


@never_cache
@allowed_methods(['POST'])
def set_public(request, podcast, public):
    settings, created = UserSettings.objects.get_or_create(
        user=request.user,
        content_type=ContentType.objects.get_for_model(podcast),
        object_id=podcast.pk,
    )
    settings.set_wksetting(PUBLIC_SUB_PODCAST, public)
    settings.save()
    return HttpResponseRedirect(get_podcast_link_target(podcast))


# To make all view accessible via either IDs or Slugs
# a decorator queries the podcast and passes the Id on to the
# regular views


def slug_decorator(f):
    @wraps(f)
    def _decorator(request, slug, *args, **kwargs):

        try:
            podcast = Podcast.objects.filter(
                slugs__slug=slug,
                slugs__content_type=ContentType.objects.get_for_model(Podcast),
            )
            podcast = podcast.prefetch_related('slugs', 'urls').get()
        except Podcast.DoesNotExist:
            raise Http404

        # redirect when a non-cannonical slug is used
        if slug != podcast.slug:
            return HttpResponseRedirect(get_podcast_link_target(podcast))

        return f(request, podcast, *args, **kwargs)

    return _decorator


def id_decorator(f):
    @wraps(f)
    def _decorator(request, podcast_id, *args, **kwargs):

        try:
            podcast = Podcast.objects.filter(id=podcast_id)
            podcast = podcast.prefetch_related('slugs', 'urls').get()

            # if the podcast has a slug, redirect to its canonical URL
            if podcast.slug:
                return HttpResponseRedirect(get_podcast_link_target(podcast))

            return f(request, podcast, *args, **kwargs)

        except Podcast.DoesNotExist:
            podcast = get_object_or_404(Podcast, merged_uuids__uuid=podcast_id)
            return HttpResponseRedirect(get_podcast_link_target(podcast))

    return _decorator


show_slug = slug_decorator(show)
subscribe_slug = slug_decorator(subscribe)
subscribe_all_slug = slug_decorator(subscribe_all)
unsubscribe_slug = slug_decorator(unsubscribe)
unsubscribe_all_slug = slug_decorator(unsubscribe_all)
add_tag_slug = slug_decorator(add_tag)
remove_tag_slug = slug_decorator(remove_tag)
set_public_slug = slug_decorator(set_public)
all_episodes_slug = slug_decorator(all_episodes)


show_id = id_decorator(show)
subscribe_id = id_decorator(subscribe)
subscribe_all_id = id_decorator(subscribe_all)
unsubscribe_id = id_decorator(unsubscribe)
unsubscribe_all_id = id_decorator(unsubscribe_all)
add_tag_id = id_decorator(add_tag)
remove_tag_id = id_decorator(remove_tag)
set_public_id = id_decorator(set_public)
all_episodes_id = id_decorator(all_episodes)
