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
from django.utils.decorators import method_decorator

from mygpo.core import models
from mygpo.core.models import Podcast, PodcastGroup
from mygpo.utils import parse_range
from mygpo.directory.tags import TagCloud
from mygpo.web.utils import get_episode_link_target, get_podcast_link_target
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.sanitizing import sanitize_url
from mygpo.api.advanced import AdvancedAPIEndpoint
from mygpo.api.backend import podcast_data, episode_data
from mygpo.directory.models import Category


class TopTagsEndpoint(AdvancedAPIEndpoint):

    @method_decorator(cache_page(60 * 60 * 24))
    def get(self, request, count):
        count = parse_range(count, 1, 100, 100)
        tag_cloud = TagCloud(count)
        resp = map(self.category_data, tag_cloud.entries)
        return resp

    def category_data(self, category):
        return dict(
            tag   = category.label,
            usage = category.weight
        )



class TopPodcastsEndpoint(AdvancedAPIEndpoint):

    @method_decorator(cache_page(60 * 60 * 24))
    def get(self, request, tag, count):
        count = parse_range(count, 1, 100, 100)
        category = Category.for_tag(tag)
        if not category:
            return []

        domain = RequestSite(request).domain
        query = category.get_podcasts(0, count)
        resp = map(lambda p: podcast_data(p, domain), query)
        return resp


class PodcastInfoEndpoint(AdvancedAPIEndpoint):

    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        url = sanitize_url(request.GET.get('url', ''))
        podcast = Podcast.for_url(url)
        if not podcast:
            raise Http404

        domain = RequestSite(request).domain
        resp = podcast_data(podcast, domain)

        return resp


class EpisodeInfoEndpoint(AdvancedAPIEndpoint):

    @method_decorator(cache_page(60 * 60))
    def get(self, request):
        podcast_url = sanitize_url(request.GET.get('podcast', ''))
        episode_url = sanitize_url(request.GET.get('url', ''), 'episode')

        episode = models.Episode.for_podcast_url(podcast_url, episode_url)

        if episode is None:
            raise Http404

        domain = RequestSite(request).domain
        resp = episode_data(episode, domain)
        return resp
