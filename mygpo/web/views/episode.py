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
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, Http404, HttpResponseForbidden
from django.template import RequestContext
from mygpo.api.models import Podcast, Episode, Device, EpisodeAction, Subscription
from mygpo.api.models.episodes import Chapter
from mygpo.api.models.users import EpisodeFavorite
from mygpo.web.models import SecurityToken
from mygpo.web.utils import get_played_parts
from mygpo.utils import parse_time
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from datetime import datetime, date, timedelta
from django.contrib.sites.models import Site
import random
import string

def episode(request, id):
    episode = get_object_or_404(Episode, pk=id)

    if request.user.is_authenticated():
        history = EpisodeAction.objects.filter(user=request.user, episode=episode).order_by('-timestamp')
        subscription_tmp = Subscription.objects.filter(podcast=episode.podcast, user=request.user)
        if subscription_tmp.exists():
            subscription_meta = subscription_tmp[0].get_meta()
        else:
            subscription_meta = None
        is_fav = EpisodeFavorite.objects.filter(user=request.user, episode=episode).exists()

        played_parts, duration = get_played_parts(request.user, episode)

    else:
        history = []
        subscription_meta = None
        is_fav = False
        played_parts = None
        duration = episode.duration

    chapters = [c for c in Chapter.objects.filter(episode=episode).order_by('start') if c.is_public() or c.user == request.user]

    return render_to_response('episode.html', {
        'episode': episode,
        'history': history,
        'chapters': chapters,
        'subscription_meta': subscription_meta,
        'is_favorite': is_fav,
        'played_parts': played_parts,
        'duration': duration
    }, context_instance=RequestContext(request))


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


@login_required
def remove_chapter(request, id, chapter_id):
    Chapter.objects.filter(user=request.user, id=chapter_id).delete()

    return HttpResponseRedirect('/episode/%s' % id)


@login_required
def toggle_favorite(request, id):
    episode = get_object_or_404(Episode, id=id)
    fav, c = EpisodeFavorite.objects.get_or_create(user=request.user, episode=episode)
    if not c:
        fav.delete()

    return HttpResponseRedirect('/episode/%s' % id)


@login_required
def list_favorites(request):
    site = Site.objects.get_current()
    episodes = [x.episode for x in EpisodeFavorite.objects.filter(user=request.user).order_by('-created')]

    token, c = SecurityToken.objects.get_or_create(user=request.user, object='fav-feed', action='r', \
        defaults={'token': "".join(random.sample(string.letters+string.digits, 8))})

    feed_url = 'http://%s/user/%s/favorites.xml' % (site.domain, request.user)

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
        'feed_url': feed_url,
        'podcast': podcast,
        }, context_instance=RequestContext(request))

