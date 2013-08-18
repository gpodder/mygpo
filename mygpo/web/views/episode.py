#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

from datetime import datetime
from functools import wraps

import dateutil.parser

from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control
from django.contrib import messages
from django.utils.translation import ugettext as _

from mygpo.api.constants import EPISODE_ACTION_TYPES
from mygpo.decorators import repeat_on_conflict
from mygpo.core.proxy import proxy_object
from mygpo.core.tasks import flattr_thing
from mygpo.users.models import Chapter, HistoryEntry, EpisodeAction
from mygpo.utils import parse_time, get_timestamp
from mygpo.users.settings import FLATTR_TOKEN
from mygpo.web.heatmap import EpisodeHeatmap
from mygpo.publisher.utils import check_publisher_permission
from mygpo.web.utils import get_episode_link_target, fetch_episode_data
from mygpo.db.couchdb.episode import episode_for_slug_id, episode_for_oldid, \
         favorite_episodes_for_user, chapters_for_episode
from mygpo.db.couchdb.podcast import podcast_by_id, podcast_for_url, \
         podcasts_to_dict
from mygpo.db.couchdb.episode_state import episode_state_for_user_episode, \
         add_episode_actions
from mygpo.db.couchdb.user import get_latest_episodes
from mygpo.userfeeds.feeds import FavoriteFeed


@vary_on_cookie
@cache_control(private=True)
def episode(request, episode):

    podcast = podcast_by_id(episode.podcast)
    user = request.user

    if not podcast:
        raise Http404

    if user.is_authenticated():

        episode_state = episode_state_for_user_episode(user, episode)
        is_fav = episode_state.is_favorite()


        # pre-populate data for fetch_data
        podcasts_dict = {podcast.get_id(): podcast}
        episodes_dict = {episode._id: episode}

        has_history = bool(list(episode_state.get_history_entries()))

        played_parts = EpisodeHeatmap(podcast.get_id(),
                episode._id, user._id, duration=episode.duration)

        devices = dict( (d.id, d.name) for d in user.devices )
        can_flattr = user.get_wksetting(FLATTR_TOKEN) and episode.flattr_url

    else:
        has_history = False
        is_fav = False
        played_parts = None
        devices = {}
        can_flattr = False

    is_publisher = check_publisher_permission(user, podcast)

    chapters = []
    for user_id, chapter in chapters_for_episode(episode._id):
        chapter.is_own = user.is_authenticated() and \
                         user_id == user._id
        chapters.append(chapter)


    prev = podcast.get_episode_before(episode)
    next = podcast.get_episode_after(episode)

    return render(request, 'episode.html', {
        'episode': episode,
        'podcast': podcast,
        'prev': prev,
        'next': next,
        'has_history': has_history,
        'chapters': chapters,
        'is_favorite': is_fav,
        'played_parts': played_parts,
        'actions': EPISODE_ACTION_TYPES,
        'devices': devices,
        'can_flattr': can_flattr,
        'is_publisher': is_publisher,
    })


@never_cache
@login_required
@vary_on_cookie
@cache_control(private=True)
def history(request, episode):
    """ shows the history of the episode """

    user = request.user
    podcast = podcast_by_id(episode.podcast)
    episode_state = episode_state_for_user_episode(user, episode)

    # pre-populate data for fetch_data
    podcasts_dict = {podcast.get_id(): podcast}
    episodes_dict = {episode._id: episode}

    history = list(episode_state.get_history_entries())
    HistoryEntry.fetch_data(user, history,
            podcasts=podcasts_dict, episodes=episodes_dict)

    devices = dict( (d.id, d.name) for d in user.devices )

    return render(request, 'episode-history.html', {
        'episode': episode,
        'podcast': podcast,
        'history': history,
        'actions': EPISODE_ACTION_TYPES,
        'devices': devices,
    })



@never_cache
@login_required
def add_chapter(request, episode):
    e_state = episode_state_for_user_episode(request.user, episode)

    podcast = podcast_by_id(episode.podcast)

    try:
        start = parse_time(request.POST.get('start', '0'))

        if request.POST.get('end', '0'):
            end = parse_time(request.POST.get('end', '0'))
        else:
            end = start

        adv = 'advertisement' in request.POST
        label = request.POST.get('label')

    except ValueError as e:
        messages.error(request,
                _('Could not add Chapter: {msg}'.format(msg=str(e))))

        return HttpResponseRedirect(get_episode_link_target(episode, podcast))


    chapter = Chapter()
    chapter.start = start
    chapter.end = end
    chapter.advertisement = adv
    chapter.label = label

    e_state.update_chapters(add=[chapter])

    return HttpResponseRedirect(get_episode_link_target(episode, podcast))


@never_cache
@login_required
def remove_chapter(request, episode, start, end):
    e_state = episode_state_for_user_episode(request.user, episode)

    remove = (int(start), int(end))
    e_state.update_chapters(rem=[remove])

    podcast = podcast_by_id(episode.podcast)

    return HttpResponseRedirect(get_episode_link_target(episode, podcast))


@never_cache
@login_required
def toggle_favorite(request, episode):
    episode_state = episode_state_for_user_episode(request.user, episode)

    @repeat_on_conflict(['episode_state'])
    def _set_fav(episode_state, is_fav):
        episode_state.set_favorite(is_fav)
        episode_state.save()

    is_fav = episode_state.is_favorite()
    _set_fav(episode_state=episode_state, is_fav=not is_fav)

    podcast = podcast_by_id(episode.podcast)

    return HttpResponseRedirect(get_episode_link_target(episode, podcast))



@vary_on_cookie
@cache_control(private=True)
@login_required
def list_favorites(request):
    user = request.user
    site = RequestSite(request)

    episodes = favorite_episodes_for_user(user)

    recently_listened = get_latest_episodes(user)

    podcast_ids = [episode.podcast for episode in episodes + recently_listened]
    podcasts = podcasts_to_dict(podcast_ids)

    recently_listened = fetch_episode_data(recently_listened, podcasts=podcasts)
    episodes = fetch_episode_data(episodes, podcasts=podcasts)

    favfeed = FavoriteFeed(user)
    feed_url = favfeed.get_public_url(site.domain)

    podcast = podcast_for_url(feed_url)

    token = request.user.favorite_feeds_token

    return render(request, 'favorites.html', {
        'episodes': episodes,
        'feed_token': token,
        'site': site,
        'podcast': podcast,
        'recently_listened': recently_listened,
        })


@never_cache
def add_action(request, episode):

    device = request.user.get_device(request.POST.get('device'))

    action_str = request.POST.get('action')
    timestamp = request.POST.get('timestamp', '')

    if timestamp:
        try:
            timestamp = dateutil.parser.parse(timestamp)
        except (ValueError, AttributeError):
            timestamp = datetime.utcnow()
    else:
        timestamp = datetime.utcnow()

    action = EpisodeAction()
    action.timestamp = timestamp
    action.upload_timestamp = get_timestamp(datetime.utcnow())
    action.device = device.id if device else None
    action.action = action_str

    state = episode_state_for_user_episode(request.user, episode)
    add_episode_actions(state, [action])

    podcast = podcast_by_id(episode.podcast)
    return HttpResponseRedirect(get_episode_link_target(episode, podcast))


@never_cache
@login_required
def flattr_episode(request, episode):
    """ Flattrs an episode, records an event and redirects to the episode """

    user = request.user
    site = RequestSite(request)

    # Flattr via the tasks queue, but wait for the result
    task = flattr_thing.delay(user, episode._id, site.domain,
            request.is_secure(), 'Episode')
    success, msg = task.get()

    if success:
        action = EpisodeAction()
        action.action = 'flattr'
        action.upload_timestamp = get_timestamp(datetime.utcnow())
        state = episode_state_for_user_episode(request.user, episode)
        add_episode_actions(state, [action])
        messages.success(request, _("Flattr\'d"))

    else:
        messages.error(request, msg)

    podcast = podcast_by_id(episode.podcast)
    return HttpResponseRedirect(get_episode_link_target(episode, podcast))


# To make all view accessible via either CouchDB-ID for Slugs
# a decorator queries the episode and passes the Id on to the
# regular views

def slug_id_decorator(f):
    @wraps(f)
    def _decorator(request, p_slug_id, e_slug_id, *args, **kwargs):
        episode = episode_for_slug_id(p_slug_id, e_slug_id)

        if episode is None:
            raise Http404

        # redirect when Id or a merged (non-cannonical) slug is used
        if episode.slug and episode.slug != e_slug_id:
            podcast = podcast_by_id(episode.podcast)
            return HttpResponseRedirect(
                    get_episode_link_target(episode, podcast))

        return f(request, episode, *args, **kwargs)

    return _decorator


def oldid_decorator(f):
    @wraps(f)
    def _decorator(request, id, *args, **kwargs):
        episode = episode_for_oldid(id)

        if episode is None:
            raise Http404

        # redirect to Id or slug URL
        podcast = podcast_by_id(episode.podcast)
        return HttpResponseRedirect(get_episode_link_target(episode, podcast))

    return _decorator

show_slug_id            = slug_id_decorator(episode)
add_chapter_slug_id     = slug_id_decorator(add_chapter)
remove_chapter_slug_id  = slug_id_decorator(remove_chapter)
toggle_favorite_slug_id = slug_id_decorator(toggle_favorite)
add_action_slug_id      = slug_id_decorator(add_action)
flattr_episode_slug_id  = slug_id_decorator(flattr_episode)
episode_history_slug_id = slug_id_decorator(history)

show_oldid            = oldid_decorator(episode)
add_chapter_oldid     = oldid_decorator(add_chapter)
remove_chapter_oldid  = oldid_decorator(remove_chapter)
toggle_favorite_oldid = oldid_decorator(toggle_favorite)
add_action_oldid      = oldid_decorator(add_action)
flattr_episode_oldid  = oldid_decorator(flattr_episode)
episode_history_oldid = oldid_decorator(history)
