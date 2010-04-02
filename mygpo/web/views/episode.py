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
from mygpo.utils import parse_time
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from datetime import datetime, date, timedelta
from django.contrib.sites.models import Site

def episode(request, id):
    episode = get_object_or_404(Episode, pk=id)

    if request.user.is_authenticated():
        history = EpisodeAction.objects.filter(user=request.user, episode=episode).order_by('-timestamp')
        subscription_tmp = Subscription.objects.filter(podcast=episode.podcast, user=request.user)
        if subscription_tmp.exists():
            subscription_meta = subscription_tmp[0].get_meta()
        else:
            subscription_meta = None
    else:
        history = []
        subscription_meta = None

    chapters = [c for c in Chapter.objects.filter(episode=episode).order_by('start') if c.is_public() or c.user == request.user]

    return render_to_response('episode.html', {
        'episode': episode,
        'history': history,
        'chapters': chapters,
        'subscription_meta': subscription_meta,
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

