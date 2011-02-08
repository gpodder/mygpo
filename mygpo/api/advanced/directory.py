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

from mygpo.api.httpresponse import JsonResponse
from django.shortcuts import get_object_or_404
from mygpo.api.sanitizing import sanitize_url
from mygpo.api.models import Podcast, Episode
from mygpo.data.models import DirectoryEntry
from mygpo.directory.models import Category
from django.contrib.sites.models import RequestSite
from django.views.decorators.csrf import csrf_exempt
from mygpo.core import models


@csrf_exempt
def top_tags(request, count):
    tags = Category.top_categories(int(count))
    resp = map(category_data, tags)
    return JsonResponse(resp)


@csrf_exempt
def tag_podcasts(request, tag, count):
    category = Category.for_tag(tag)
    if not category:
        return JsonResponse([])

    domain = RequestSite(request).domain
    query = DirectoryEntry.objects.podcasts_for_category(category.get_tags())[:int(count)]
    resp = map(lambda p: podcast_data(p.get_podcast(), domain), query)
    return JsonResponse(resp)


def podcast_info(request):
    url = sanitize_url(request.GET.get('url', ''))
    podcast = get_object_or_404(Podcast, url=url)
    domain = RequestSite(request).domain
    resp = podcast_data(podcast, domain)

    return JsonResponse(resp)


def episode_info(request):
    podcast_url = sanitize_url(request.GET.get('podcast', ''))
    episode_url = sanitize_url(request.GET.get('url', ''), podcast=False, episode=True)
    episode = get_object_or_404(Episode, url=episode_url, podcast__url=podcast_url)
    domain = RequestSite(request).domain

    resp = episode_data(episode, domain)
    return JsonResponse(resp)


def podcast_data(podcast, domain):
    if podcast.group:
        obj = models.PodcastGroup.for_oldid(podcast.group.id)
    else:
        obj = models.Podcast.for_oldid(podcast.id)

    subscribers = obj.subscriber_count()
    last_subscribers = obj.prev_subscriber_count()

    return {
        "url": podcast.url,
        "title": podcast.title,
        "description": podcast.description,
        "subscribers": subscribers,
        "subscribers_last_week": last_subscribers,
        "logo_url": podcast.logo_url,
        "website": podcast.link,
        "mygpo_link": 'http://%s/podcast/%s' % (domain, podcast.id),
        }

def episode_data(episode, domain):
    data = {
        "title": episode.title,
        "url": episode.url,
        "podcast_title": episode.podcast.title,
        "podcast_url": episode.podcast.url,
        "description": episode.description,
        "website": episode.link,
        "mygpo_link": 'http://%s/episode/%s' % (domain, episode.id),
        }

    if episode.timestamp:
        data['released'] = episode.timestamp.strftime('%Y-%m-%dT%H:%M:%S')

    return data


def category_data(category):
    return dict(
        tag   = category.label,
        usage = category.weight
    )

