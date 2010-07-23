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

from mygpo.api.basic_auth import require_valid_user, check_username
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404, HttpResponseNotAllowed
from mygpo.api.httpresponse import JsonResponse
from mygpo.exceptions import ParameterMissing
from django.shortcuts import get_object_or_404
from mygpo.api.sanitizing import sanitize_url
from mygpo.api.models import Device, Podcast, Episode, ToplistEntry
from mygpo.api.models.episodes import Chapter
from mygpo.data.models import PodcastTag
from django.utils.translation import ugettext as _
from datetime import datetime, timedelta
from mygpo.log import log
from mygpo.utils import parse_time
import dateutil.parser
from django.contrib.sites.models import Site
from django.views.decorators.csrf import csrf_exempt

try:
    #try to import the JSON module (if we are on Python 2.6)
    import json

    # Python 2.5 seems to have a different json module
    if not 'dumps' in dir(json):
        raise ImportError

except ImportError:
    # No JSON module available - fallback to simplejson (Python < 2.6)
    print "No JSON module available - fallback to simplejson (Python < 2.6)"
    import simplejson as json


@csrf_exempt
def top_tags(request, count):
    tags = DirectoryEntry.objects.top_tags(int(count))
    resp = []
    for t in tags:
        resp.append( {
            'tag': t.tag,
            'usage': t.entries
            } )
    return JsonResponse(resp)


@csrf_exempt
def tag_podcasts(request, tag, count):
    resp = []
    for p in DirectoryEntry.objects.podcasts_for_tag(tag)[:int(count)]:
        resp.append( podcast_data(p.get_podcast()) )

    return JsonResponse(resp)


def podcast_info(request):
    url = sanitize_url(request.GET.get('url', ''))
    podcast = get_object_or_404(Podcast, url=url)
    resp = podcast_data(podcast)

    return JsonResponse(resp)


def episode_info(request):
    podcast_url = sanitize_url(request.GET.get('podcast', ''))
    episode_url = sanitize_url(request.GET.get('url', ''), podcast=False, episode=True)
    episode = get_object_or_404(Episode, url=episode_url, podcast__url=podcast_url)

    resp = episode_data(episode)
    return JsonResponse(resp)


def podcast_data(podcast):
    site = Site.objects.get_current()
    if podcast.group:
        try:
            e = ToplistEntry.objects.get(podcast_group=podcast.group)

        # no toplist entry has been created for the group yet
        except ToplistEntry.DoesNotExist:
            e = ToplistEntry.objects.get(podcast=podcast)
    else:
        e = ToplistEntry.objects.get(podcast=podcast)

    return {
        "url": podcast.url,
        "title": podcast.title,
        "description": podcast.description,
        "subscribers": e.subscriptions,
        "logo_url": podcast.logo_url,
        "website": podcast.link,
        "mygpo_link": 'http://%s/podcast/%s' % (site.domain, podcast.id),
        }

def episode_data(episode):
    site = Site.objects.get_current()

    return {
        "title": episode.title,
        "url": episode.url,
        "podcast_title": episode.podcast.title,
        "podcast_url": episode.podcast.url,
        "description": episode.description,
        "website": episode.link,
        "mygpo_link": 'http://%s/episode/%s' % (site.domain, episode.id),
        }
