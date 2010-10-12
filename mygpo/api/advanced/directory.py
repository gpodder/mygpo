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
from mygpo.api.models import Podcast, Episode, ToplistEntry
from mygpo.data.models import DirectoryEntry
from mygpo.directory.models import Category
from django.contrib.sites.models import Site
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def top_tags(request, count):
    tags = Category.top_categories(int(count))
    resp = map(category_data, tags)
    return JsonResponse(resp)


@csrf_exempt
def tag_podcasts(request, tag, count):
    category = Category.for_tag(tag)
    query = DirectoryEntry.objects.podcasts_for_category(category.get_tags())[:int(count)]
    resp = map(lambda p: podcast_data(p.get_podcast()), query)
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
            subscribers = ToplistEntry.objects.get(podcast_group=podcast.group).subscriptions

        # no toplist entry has been created for the group yet
        except ToplistEntry.DoesNotExist:
            subscribers = ToplistEntry.objects.get(podcast=podcast).subscriptions
    else:
        try:
            subscribers = ToplistEntry.objects.get(podcast=podcast).subscriptions
        # no toplist entry has been created for this podcast yet
        except ToplistEntry.DoesNotExist:
            subscribers = 0

    return {
        "url": podcast.url,
        "title": podcast.title,
        "description": podcast.description,
        "subscribers": subscribers,
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


def category_data(category):
    return dict(
        tag   = category.label,
        usage = category.weight
    )

