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

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite

from mygpo.api.constants import EPISODE_ACTION_TYPES
from mygpo.decorators import repeat_on_conflict
from mygpo.core import models
from mygpo.core.models import Podcast
from mygpo.core.proxy import proxy_object
from mygpo.core.models import Episode
from mygpo.users.models import Chapter, HistoryEntry, EpisodeAction
from mygpo.api import backend
from mygpo.utils import parse_time, get_to_dict, get_timestamp
from mygpo.web.heatmap import EpisodeHeatmap
from mygpo.web.utils import get_episode_link_target


def episode(request, episode):

    podcast = Podcast.get(episode.podcast)

    if not podcast:
        raise Http404

    if request.user.is_authenticated():

        episode_state = episode.get_user_state(request.user)
        is_fav = episode_state.is_favorite()


        # pre-populate data for fetch_data
        podcasts_dict = {podcast.get_id(): podcast}
        episodes_dict = {episode._id: episode}

        history = list(episode_state.get_history_entries())
        HistoryEntry.fetch_data(request.user, history,
                podcasts=podcasts_dict, episodes=episodes_dict)

        played_parts = EpisodeHeatmap(podcast.get_id(),
                episode._id, request.user._id, duration=episode.duration)

        devices = dict( (d.id, d.name) for d in request.user.devices )

    else:
        history = []
        is_fav = False
        played_parts = None
        devices = {}


    chapters = []
    for user, chapter in Chapter.for_episode(episode._id):
        chapter.is_own = request.user.is_authenticated() and \
                         user == request.user._id
        chapters.append(chapter)


    prev = podcast.get_episode_before(episode)
    next = podcast.get_episode_after(episode)

    return render_to_response('episode.html', {
        'episode': episode,
        'podcast': podcast,
        'prev': prev,
        'next': next,
        'history': history,
        'chapters': chapters,
        'is_favorite': is_fav,
        'played_parts': played_parts,
        'actions': EPISODE_ACTION_TYPES,
        'devices': devices,
    }, context_instance=RequestContext(request))


@login_required
def add_chapter(request, episode):
    e_state = episode.get_user_state(request.user)

    podcast = Podcast.get(episode.podcast)

    try:
        start = parse_time(request.POST.get('start', '0'))

        if request.POST.get('end', '0'):
            end = parse_time(request.POST.get('end', '0'))
        else:
            end = start

        adv = 'advertisement' in request.POST
        label = request.POST.get('label')

    except Exception as e:
        # FIXME: when using Django's messaging system, set error message

        return HttpResponseRedirect(get_episode_link_target(episode, podcast))


    chapter = Chapter()
    chapter.start = start
    chapter.end = end
    chapter.advertisement = adv
    chapter.label = label

    e_state.update_chapters(add=[chapter])

    return HttpResponseRedirect(get_episode_link_target(episode, podcast))


@login_required
def remove_chapter(request, episode, start, end):
    e_state = episode.get_user_state(request.user)

    remove = (int(start), int(end))
    e_state.update_chapters(rem=[remove])

    podcast = Podcast.get(episode.podcast)

    return HttpResponseRedirect(get_episode_link_target(episode, podcast))


@login_required
def toggle_favorite(request, episode):
    episode_state = episode.get_user_state(request.user)
    is_fav = episode_state.is_favorite()
    episode_state.set_favorite(not is_fav)

    episode_state.save()

    podcast = Podcast.get(episode.podcast)

    return HttpResponseRedirect(get_episode_link_target(episode, podcast))


@login_required
def list_favorites(request):
    site = RequestSite(request)

    episodes = backend.get_favorites(request.user)
    podcast_ids = [episode.podcast for episode in episodes]
    podcasts = get_to_dict(Podcast, podcast_ids, Podcast.get_id)

    def set_podcast(episode):
        episode = proxy_object(episode)
        episode.podcast = podcasts.get(episode.podcast, None)
        return episode

    episodes = map(set_podcast, episodes)

    feed_url = 'http://%s/%s' % (site.domain, reverse('favorites-feed', args=[request.user.username]))

    podcast = Podcast.for_url(feed_url)

    if 'public_feed' in request.GET:
        request.user.favorite_feeds_token = ''
        request.user.save()

    elif 'private_feed' in request.GET:
        request.user.create_new_token('favorite_feeds_token', 8)
        request.user.save()

    token = request.user.favorite_feeds_token

    return render_to_response('favorites.html', {
        'episodes': episodes,
        'feed_token': token,
        'site': site,
        'podcast': podcast,
        }, context_instance=RequestContext(request))


def add_action(request, episode):

    device = request.user.get_device(request.POST.get('device'))

    action_str = request.POST.get('action')
    timestamp = request.POST.get('timestamp', '')

    if timestamp:
        try:
            timestamp = dateutil.parser.parse(timestamp)
        except:
            timestamp = datetime.utcnow()
    else:
        timestamp = datetime.utcnow()

    action = EpisodeAction()
    action.timestamp = timestamp
    action.upload_timestamp = get_timestamp(datetime.utcnow())
    action.device = device.id if device else None
    action.action = action_str

    state = episode.get_user_state(request.user)

    @repeat_on_conflict(['action'])
    def _add_action(action):
        state.add_actions([action])
        state.save()

    _add_action(action=action)

    podcast = Podcast.get(episode.podcast)

    return HttpResponseRedirect(get_episode_link_target(episode, podcast))

# To make all view accessible via either CouchDB-ID for Slugs
# a decorator queries the episode and passes the Id on to the
# regular views

def slug_id_decorator(f):
    @wraps(f)
    def _decorator(request, p_slug_id, e_slug_id, *args, **kwargs):
        episode = Episode.for_slug_id(p_slug_id, e_slug_id)

        if episode is None:
            raise Http404

        return f(request, episode, *args, **kwargs)

    return _decorator


def oldid_decorator(f):
    @wraps(f)
    def _decorator(request, id, *args, **kwargs):
        episode = Episode.for_oldid(id)

        if episode is None:
            raise Http404

        return f(request, episode, *args, **kwargs)

    return _decorator

show_slug_id            = slug_id_decorator(episode)
add_chapter_slug_id     = slug_id_decorator(add_chapter)
remove_chapter_slug_id  = slug_id_decorator(remove_chapter)
toggle_favorite_slug_id = slug_id_decorator(toggle_favorite)
add_action_slug_id      = slug_id_decorator(add_action)

show_oldid            = oldid_decorator(episode)
add_chapter_oldid     = oldid_decorator(add_chapter)
remove_chapter_oldid  = oldid_decorator(remove_chapter)
toggle_favorite_oldid = oldid_decorator(toggle_favorite)
add_action_oldid      = oldid_decorator(add_action)
