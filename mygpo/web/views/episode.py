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

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from mygpo.core import models
from mygpo.api.models import Podcast, Episode, EpisodeAction, Subscription
from mygpo.api.models.episodes import Chapter
from mygpo.api import backend
from mygpo.web.models import SecurityToken
from mygpo.web.utils import get_played_parts
from mygpo.decorators import manual_gc
from mygpo.utils import parse_time
from mygpo import migrate
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.sites.models import RequestSite

@manual_gc
def episode(request, id):
    episode = get_object_or_404(Episode, pk=id)

    if request.user.is_authenticated():
        history = EpisodeAction.objects.filter(user=request.user, episode=episode).order_by('-timestamp')
        subscription_tmp = Subscription.objects.filter(podcast=episode.podcast, user=request.user)
        if subscription_tmp.exists():
            subscription_meta = subscription_tmp[0].get_meta()
        else:
            subscription_meta = None

        new_ep  = migrate.get_or_migrate_episode(episode)
        podcast = models.Podcast.for_oldid(episode.podcast.id)
        episode_state = migrate.get_episode_user_state(request.user, new_ep._id, podcast)
        is_fav = episode_state.is_favorite()

        played_parts, duration = get_played_parts(request.user, episode)

    else:
        history = []
        subscription_meta = None
        is_fav = False
        played_parts = None
        duration = episode.duration

    chapters = [c for c in Chapter.objects.filter(episode=episode).order_by('start') if c.is_public() or c.user == request.user]
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
        'subscription_meta': subscription_meta,
        'is_favorite': is_fav,
        'played_parts': played_parts,
        'duration': duration
    }, context_instance=RequestContext(request))


@manual_gc
@login_required
def add_chapter(request, id):
    episode = get_object_or_404(Episode, pk=id)

    try:
        start = parse_time(request.POST.get('start', '0'))

        if request.POST.get('end', '0'):
            end = parse_time(request.POST.get('end', '0'))
        else:
            end = start

        adv = 'advertisement' in request.POST
        label = request.POST.get('label')

        Chapter.objects.create(user=request.user, episode=episode, start=start, end=end, advertisement=adv, label=label)
    except:
        pass

    return HttpResponseRedirect('/episode/%s' % id)


@manual_gc
@login_required
def remove_chapter(request, id, chapter_id):
    Chapter.objects.filter(user=request.user, id=chapter_id).delete()

    return HttpResponseRedirect('/episode/%s' % id)


@manual_gc
@login_required
def toggle_favorite(request, id):
    episode = get_object_or_404(Episode, id=id)

    new_ep  = migrate.get_or_migrate_episode(episode)
    podcast = migrate.get_or_migrate_podcast(episode.podcast)
    episode_state = migrate.get_episode_user_state(request.user, new_ep._id, podcast)
    is_fav = episode_state.is_favorite()
    episode_state.set_favorite(not is_fav)

    episode_state.save()

    return HttpResponseRedirect('/episode/%s' % id)


@manual_gc
@login_required
def list_favorites(request):
    site = RequestSite(request)
    episodes = backend.get_favorites(request.user)

    token, c = SecurityToken.objects.get_or_create(user=request.user, object='fav-feed', action='r')

    from django.core.urlresolvers import reverse
    feed_url = 'http://%s/%s' % (site.domain, reverse('favorites-feed', args=[request.user.username]))

    try:
        podcast = Podcast.objects.get(url=feed_url)
    except Podcast.DoesNotExist:
        podcast = None

    if 'public_feed' in request.GET:
        token.token = ''
        token.save()

    elif 'private_feed' in request.GET:
        token.random_token(length=8)
        token.save()


    return render_to_response('favorites.html', {
        'episodes': episodes,
        'feed_token': token,
        'site': site,
        'podcast': podcast,
        }, context_instance=RequestContext(request))

