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

from django.http import Http404
from django.core.urlresolvers import reverse
from django.contrib.sites.models import RequestSite
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page

from mygpo.core import models
from mygpo.core.models import Podcast, PodcastGroup
from mygpo.utils import parse_range, normalize_feed_url
from mygpo.directory.tags import Topics
from mygpo.web.utils import get_episode_link_target, get_podcast_link_target
from mygpo.web.logo import get_logo_url
from mygpo.decorators import cors_origin
from mygpo.api.httpresponse import JsonResponse
from mygpo.db.couchdb.episode import episode_for_podcast_url
from mygpo.db.couchdb.podcast import podcast_by_id, podcast_for_url
from mygpo.db.couchdb.directory import category_for_tag


@csrf_exempt
@cache_page(60 * 60 * 24)
@cors_origin()
def top_tags(request, count):
    count = parse_range(count, 1, 100, 100)
    tag_cloud = Topics(count, num_cat=0)
    resp = map(category_data, tag_cloud.tagcloud)
    return JsonResponse(resp)


@csrf_exempt
@cache_page(60 * 60 * 24)
@cors_origin()
def tag_podcasts(request, tag, count):
    count = parse_range(count, 1, 100, 100)
    category = category_for_tag(tag)
    if not category:
        return JsonResponse([])

    domain = RequestSite(request).domain
    query = category.get_podcasts(0, count)
    resp = map(lambda p: podcast_data(p, domain), query)
    return JsonResponse(resp)


@cache_page(60 * 60)
@cors_origin()
def podcast_info(request):
    url = normalize_feed_url(request.GET.get('url', ''))

    # 404 before we query for url, because query would complain
    # about missing param
    if not url:
        raise Http404

    podcast = podcast_for_url(url)
    if not podcast:
            raise Http404
    domain = RequestSite(request).domain
    resp = podcast_data(podcast, domain)

    return JsonResponse(resp)


@cache_page(60 * 60)
@cors_origin()
def episode_info(request):
    podcast_url = normalize_feed_url(request.GET.get('podcast', ''))
    episode_url = normalize_feed_url(request.GET.get('url', ''))

    # 404 before we query for url, because query would complain
    # about missing parameters
    if not podcast_url or not episode_url:
        raise Http404

    episode = episode_for_podcast_url(podcast_url, episode_url)

    if episode is None:
        raise Http404

    domain = RequestSite(request).domain

    resp = episode_data(episode, domain)
    return JsonResponse(resp)


def podcast_data(obj, domain, scaled_logo_size=64):
    if obj is None:
        raise ValueError('podcast should not be None')

    podcast = obj.get_podcast()
    subscribers = obj.subscriber_count()
    last_subscribers = obj.prev_subscriber_count()

    scaled_logo_url = get_logo_url(obj, scaled_logo_size)

    return {
        "url": podcast.url,
        "title": podcast.title,
        "description": podcast.description,
        "subscribers": subscribers,
        "subscribers_last_week": last_subscribers,
        "logo_url": podcast.logo_url,
        "scaled_logo_url": 'http://%s%s' % (domain, scaled_logo_url),
        "website": podcast.link,
        "mygpo_link": 'http://%s%s' % (domain, get_podcast_link_target(obj)),
        }

def episode_data(episode, domain, podcast=None):

    podcast = podcast or podcast_by_id(episode.podcast)

    data = {
        "title": episode.title,
        "url": episode.url,
        "podcast_title": podcast.title if podcast else '',
        "podcast_url": podcast.url if podcast else '',
        "description": episode.description,
        "website": episode.link,
        "mygpo_link": 'http://%(domain)s%(res)s' % dict(domain=domain,
            res=get_episode_link_target(episode, podcast)) if podcast else ''
        }

    if episode.released:
        data['released'] = episode.released.strftime('%Y-%m-%dT%H:%M:%S')

    return data


def category_data(category):
    return dict(
        tag   = category.label,
        usage = category.get_weight()
    )
