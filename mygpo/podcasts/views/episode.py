from datetime import datetime
from functools import wraps

import dateutil.parser

from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.sites.requests import RequestSite
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control
from django.contrib import messages
from django.utils.translation import gettext as _

from mygpo.podcasts.models import Podcast, Episode
from mygpo.api.constants import EPISODE_ACTION_TYPES
from mygpo.utils import parse_time, get_timestamp
from mygpo.history.stats import last_played_episodes
from mygpo.publisher.utils import check_publisher_permission
from mygpo.web.utils import get_episode_link_target, check_restrictions
from mygpo.history.models import EpisodeHistoryEntry
from mygpo.favorites.models import FavoriteEpisode
from mygpo.userfeeds.feeds import FavoriteFeed


@vary_on_cookie
@cache_control(private=True)
def episode(request, episode):

    podcast = episode.podcast

    podcast = check_restrictions(podcast)

    user = request.user

    if not podcast:
        raise Http404

    if user.is_authenticated:

        is_fav = FavoriteEpisode.objects.filter(user=user, episode=episode).exists()

        # pre-populate data for fetch_data
        podcasts_dict = {podcast.get_id(): podcast}
        episodes_dict = {episode.id.hex: episode}

        has_history = EpisodeHistoryEntry.objects.filter(
            user=user, episode=episode
        ).exists()

        devices = {c.id.hex: c for c in user.client_set.all()}

    else:
        has_history = False
        is_fav = False
        devices = {}

    is_publisher = check_publisher_permission(user, podcast)

    prev = None  # podcast.get_episode_before(episode)
    next = None  # podcast.get_episode_after(episode)

    return render(
        request,
        'episode.html',
        {
            'episode': episode,
            'podcast': podcast,
            'prev': prev,
            'next': next,
            'has_history': has_history,
            'is_favorite': is_fav,
            'actions': EPISODE_ACTION_TYPES,
            'devices': devices,
            'is_publisher': is_publisher,
        },
    )


@never_cache
@login_required
@vary_on_cookie
@cache_control(private=True)
def history(request, episode):
    """ shows the history of the episode """

    user = request.user
    podcast = episode.podcast

    history = (
        EpisodeHistoryEntry.objects.filter(user=user, episode=episode)
        .order_by('-timestamp')
        .prefetch_related(
            'episode',
            'episode__slugs',
            'episode__podcast',
            'episode__podcast__slugs',
            'client',
        )
    )

    clients = user.client_set.all()

    return render(
        request,
        'episode-history.html',
        {
            'episode': episode,
            'podcast': podcast,
            'history': history,
            'actions': EPISODE_ACTION_TYPES,
            'clients': clients,
        },
    )


@never_cache
@login_required
def toggle_favorite(request, episode):
    user = request.user

    fav, created = FavoriteEpisode.objects.get_or_create(user=user, episode=episode)

    # if the episode was already a favorite, remove it
    if not created:
        fav.delete()

    podcast = episode.podcast
    return HttpResponseRedirect(get_episode_link_target(episode, podcast))


@vary_on_cookie
@cache_control(private=True)
@login_required
def list_favorites(request):
    user = request.user
    site = RequestSite(request)

    favorites = FavoriteEpisode.episodes_for_user(user)

    recently_listened = last_played_episodes(user)

    favfeed = FavoriteFeed(user)
    feed_url = favfeed.get_public_url(site.domain)

    podcast = Podcast.objects.filter(urls__url=feed_url).first()

    token = request.user.profile.favorite_feeds_token

    return render(
        request,
        'favorites.html',
        {
            'episodes': favorites,
            'feed_token': token,
            'site': site,
            'podcast': podcast,
            'recently_listened': recently_listened,
        },
    )


@never_cache
def add_action(request, episode):

    user = request.user
    client = user.client_set.get(id=request.POST.get('device'))

    action_str = request.POST.get('action')
    timestamp = request.POST.get('timestamp', '')

    if timestamp:
        try:
            timestamp = dateutil.parser.parse(timestamp)
        except (ValueError, AttributeError, TypeError):
            timestamp = datetime.utcnow()
    else:
        timestamp = datetime.utcnow()

    EpisodeHistoryEntry.create_entry(user, episode, action_str, client, timestamp)
    podcast = episode.podcast
    return HttpResponseRedirect(get_episode_link_target(episode, podcast))


# To make all view accessible via either IDs or Slugs
# a decorator queries the episode and passes the Id on to the
# regular views


def slug_decorator(f):
    @wraps(f)
    def _decorator(request, p_slug, e_slug, *args, **kwargs):

        pquery = Podcast.objects.filter(slugs__slug=p_slug, slugs__scope='')

        try:
            podcast = pquery.prefetch_related('slugs').get()
        except Podcast.DoesNotExist:
            raise Http404

        equery = Episode.objects.filter(
            podcast=podcast, slugs__slug=e_slug, slugs__scope=podcast.id.hex
        )

        try:
            episode = equery.prefetch_related('urls', 'slugs').get()

            # set previously fetched podcast, to avoid additional query
            episode.podcast = podcast

        except Episode.DoesNotExist:
            raise Http404

        # redirect when Id or a merged (non-cannonical) slug is used
        if episode.slug and episode.slug != e_slug:
            return HttpResponseRedirect(get_episode_link_target(episode, podcast))

        return f(request, episode, *args, **kwargs)

    return _decorator


def id_decorator(f):
    @wraps(f)
    def _decorator(request, p_id, e_id, *args, **kwargs):

        try:
            query = Episode.objects.filter(id=e_id, podcast_id=p_id)
            episode = query.select_related('podcast').get()

        except Episode.DoesNotExist:
            raise Http404

        # redirect when Id or a merged (non-cannonical) slug is used
        if episode.slug and episode.slug != e_id:
            podcast = episode.podcast
            return HttpResponseRedirect(get_episode_link_target(episode, podcast))

        return f(request, episode, *args, **kwargs)

    return _decorator


show_slug = slug_decorator(episode)
toggle_favorite_slug = slug_decorator(toggle_favorite)
add_action_slug = slug_decorator(add_action)
episode_history_slug = slug_decorator(history)

show_id = id_decorator(episode)
toggle_favorite_id = id_decorator(toggle_favorite)
add_action_id = id_decorator(add_action)
episode_history_id = id_decorator(history)
