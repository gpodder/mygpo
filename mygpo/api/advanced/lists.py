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

from functools import partial

from django.http import HttpResponse, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.sites.models import RequestSite
from django.template.defaultfilters import slugify
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from mygpo.api.backend import podcast_data
from mygpo.api import APIEndpoint
from mygpo.share.models import PodcastList
from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.core.models import Podcast
from mygpo.decorators import repeat_on_conflict
from mygpo.api.simple import parse_subscription, format_podcast_list, \
     check_format
from mygpo.share.views import list_decorator
from mygpo.users.models import User
from mygpo.api.exceptions import APIParameterException
from mygpo.api.advanced import AdvancedAPIEndpoint



class CreatePodcastListEndpoint(APIEndpoint):

    @method_decorator(require_valid_user)
    @method_decorator(check_username)
    @method_decorator(check_format)
    @method_decorator(never_cache)
    def post(request, username, format):
        """ Creates a new podcast list and links to it in the Location header """

        title = request.GET.get('title', None)

        if not title:
            raise ParameterMissing('Title missing')

        slug = slugify(title)

        if not slug:
            raise APIParameterException('Invalid title')

        plist = PodcastList.for_user_slug(request.user._id, slug)

        if plist:
            raise HttpResponse('List already exists', status=409)

        urls = parse_subscription(request.raw_post_data, format)
        podcasts = [Podcast.for_url(url, create=True) for url in urls]
        podcast_ids = map(Podcast.get_id, podcasts)

        plist = PodcastList()
        plist.title = title
        plist.slug = slug
        plist.user = request.user._id
        plist.podcasts = podcast_ids
        plist.save()

        response = HttpResponse(status=201)
        list_url = reverse('api-get-list', args=[request.user.username, slug, format])
        response['Location'] = list_url

        return response



class UserPodcastListsEndpoint(AdvancedAPIEndpoint):
    """ Returns a list of all podcast lists by the given user """


    @method_decorator(never_cache)
    def get(self, request, username):

        user = User.get_user(username)
        if not user:
            raise Http404

        lists = PodcastList.for_user(user._id)

        site = RequestSite(request)

        get_data = partial(self.get_list_data, username=user.username,
                    domain=site.domain)
        lists_data = map(get_data, lists)

        return lists_data


    def get_list_data(self, l, username, domain):
        return dict(
                title= l.title,
                name = l.slug,
                web  = 'http://%s%s' % (domain,
                    reverse('list-show', args=[username, l.slug])),
            )



class PodcastListEndpoint(APIEndpoint):

    @method_decorator(check_format)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(PodcastListEndpoint, self).dispatch(*args, **kwargs)


    @method_decorator(list_decorator(must_own=False))
    def get(self, request, plist, owner, format):
        """ Returns the contents of the podcast list """

        try:
            scale = int(request.GET.get('scale_logo', 64))
        except (TypeError, ValueError):
            raise APIParameterException('scale_logo has to be a numeric value')

        podcasts = Podcast.get_multi(plist.podcasts)

        domain = RequestSite(request).domain
        p_data = lambda p: podcast_data(p, domain, scale)
        title = '{title} by {username}'.format(title=plist.title,
                username=owner.username)

        return format_podcast_list(podcasts, format, title, json_map=p_data,
                jsonp_padding=request.GET.get('jsonp', ''),
                xml_template='podcasts.xml', request=request)


    @method_decorator(require_valid_user)
    @method_decorator(list_decorator(must_own=True))
    def put(self, request, plist, owner, format):
        """ Replaces the podcasts in the list and returns 204 No Content """

        is_own = owner == request.uuser

        if not is_own:
            return HttpResponseForbidden()

        urls = parse_subscription(request.raw_post_data, format)
        podcasts = [Podcast.for_url(url, create=True) for url in urls]
        podcast_ids = map(Podcast.get_id, podcasts)

        @repeat_on_conflict(['podcast_ids'])
        def _update(plist, podcast_ids):
            plist.podcasts = podcast_ids
            plist.save()

        _update(plist=plist, podcast_ids=podcast_ids)

        return HttpResponse(status=204)


    @method_decorator(require_valid_user)
    @method_decorator(list_decorator(must_own=True))
    def delete(self, request, plist, owner, format):
        """ Delete the podcast list and returns 204 No Content """

        is_own = owner == request.user

        if not is_own:
            return HttpResponseForbidden()

        self._delete(plist=plist)

        return HttpResponse(status=204)

    @repeat_on_conflict(['plist'])
    def _delete(self, plist):
        plist.delete()
