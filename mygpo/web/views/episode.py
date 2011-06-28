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

import dateutil.parser

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse

from mygpo.core import models
from mygpo.api.models import Podcast, Episode
from mygpo.users.models import Chapter, HistoryEntry, EpisodeAction
from mygpo.api import backend
from mygpo.decorators import manual_gc
from mygpo.utils import parse_time
from mygpo import migrate
from mygpo.web.heatmap import EpisodeHeatmap
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import RequestSite
from mygpo.api.constants import EPISODE_ACTION_TYPES
from mygpo.decorators import repeat_on_conflict



@manual_gc
def episode(request, id):
    episode = get_object_or_404(Episode, pk=id)
    new_episode = migrate.get_or_migrate_episode(episode)
    podcast = migrate.get_or_migrate_podcast(episode.podcast)

    if request.user.is_authenticated():

        user = migrate.get_or_migrate_user(request.user)

        episode_state = new_episode.get_user_state(request.user)
        is_fav = episode_state.is_favorite()

        history = list(episode_state.get_history_entries())
        HistoryEntry.fetch_data(user, history)

        played_parts = EpisodeHeatmap(podcast.get_id(),
                new_episode._id, user.oldid, duration=new_episode.duration)

        devices = dict( (d.id, d.name) for d in user.devices )

    else:
        history = []
        is_fav = False
        played_parts = None
        devices = {}


    chapters = []
    for user, chapter in Chapter.for_episode(new_episode._id):
        chapter.is_own = user == request.user.id
        chapters.append(chapter)


    if episode.timestamp:
        prevs = Episode.objects.filter(podcast=episode.podcast,
                timestamp__lt=episode.timestamp, title__isnull=False)\
                .exclude(title='').order_by('-timestamp')
        prev = prevs[0] if prevs else None

        nexts = Episode.objects.filter(podcast=episode.podcast,
                timestamp__gt=episode.timestamp, title__isnull=False)\
                .exclude(title='').order_by('timestamp')
        next = nexts[0] if nexts else None
    else:
        prev = None
        next = None

    return render_to_response('episode.html', {
        'episode': episode,
        'prev': prev,
        'next': next,
        'history': history,
        'chapters': chapters,
        'is_favorite': is_fav,
        'played_parts': played_parts,
        'actions': EPISODE_ACTION_TYPES,
        'devices': devices,
    }, context_instance=RequestContext(request))


@manual_gc
@login_required
def add_chapter(request, id):
    episode = get_object_or_404(Episode, pk=id)
    new_episode = migrate.get_or_migrate_episode(episode)
    e_state = new_episode.get_user_state(request.user)

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

        return HttpResponseRedirect('/episode/%s' % id)


    chapter = Chapter()
    chapter.start = start
    chapter.end = end
    chapter.advertisement = adv
    chapter.label = label

    e_state.update_chapters(add=[chapter])

    return HttpResponseRedirect('/episode/%s' % id)


@manual_gc
@login_required
def remove_chapter(request, id, start, end):
    episode = get_object_or_404(Episode, pk=id)
    new_episode = migrate.get_or_migrate_episode(episode)
    e_state = new_episode.get_user_state(request.user)

    remove = (int(start), int(end))
    e_state.update_chapters(rem=[remove])

    return HttpResponseRedirect('/episode/%s' % id)


@manual_gc
@login_required
def toggle_favorite(request, id):
    episode = get_object_or_404(Episode, id=id)

    new_ep  = migrate.get_or_migrate_episode(episode)
    podcast = migrate.get_or_migrate_podcast(episode.podcast)
    episode_state = migrate.get_episode_user_state(request.user, new_ep, podcast)
    is_fav = episode_state.is_favorite()
    episode_state.set_favorite(not is_fav)

    episode_state.save()

    return HttpResponseRedirect('/episode/%s' % id)


@manual_gc
@login_required
def list_favorites(request):
    site = RequestSite(request)
    episodes = backend.get_favorites(request.user)

    user = migrate.get_or_migrate_user(request.user)

    feed_url = 'http://%s/%s' % (site.domain, reverse('favorites-feed', args=[request.user.username]))

    try:
        podcast = Podcast.objects.get(url=feed_url)
    except Podcast.DoesNotExist:
        podcast = None

    if 'public_feed' in request.GET:
        user.favorite_feeds_token = ''
        user.save()

    elif 'private_feed' in request.GET:
        user.create_new_token('favorite_feeds_token', 8)
        user.save()

    token = user.favorite_feeds_token

    return render_to_response('favorites.html', {
        'episodes': episodes,
        'feed_token': token,
        'site': site,
        'podcast': podcast,
        }, context_instance=RequestContext(request))


def add_action(request, id):
    episode = get_object_or_404(Episode, id=id)
    episode = migrate.get_or_migrate_episode(episode)

    user = migrate.get_or_migrate_user(request.user)
    device = user.get_device(request.POST.get('device'))

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
    action.device_oldid = device.oldid if device else None
    action.action = action_str

    state = episode.get_user_state(request.user)

    @repeat_on_conflict(['action'])
    def _add_action(action):
        state.add_actions([action])
        state.save()

    _add_action(action=action)

    return HttpResponseRedirect(reverse('episode', args=[id]))

# To make all view accessible via either CouchDB-ID for Slugs
# a decorator queries the episode and passes the Id on to the
# regular views

def slug_id_decorator(f):
    def _decorator(request, p_slug_id, e_slug_id, *args, **kwargs):
        episode = models.Episode.for_slug_id(p_slug_id, e_slug_id)
        return f(request, episode.oldid, *args, **kwargs)

    return _decorator


show_slug_id            = slug_id_decorator(episode)
add_chapter_slug_id     = slug_id_decorator(add_chapter)
remove_chapter_slug_id  = slug_id_decorator(remove_chapter)
toggle_favorite_slug_id = slug_id_decorator(toggle_favorite)
