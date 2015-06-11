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

import uuid
from functools import partial
from datetime import datetime

from django.http import HttpResponse, HttpResponseBadRequest, \
     HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.contrib.sites.requests import RequestSite
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.http import Http404
from django.shortcuts import get_object_or_404

from mygpo.podcasts.models import Podcast
from mygpo.utils import get_timestamp
from mygpo.api.advanced.directory import podcast_data
from mygpo.api.httpresponse import JsonResponse
from mygpo.podcastlists.models import PodcastList
from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.decorators import allowed_methods, cors_origin
from mygpo.api.simple import parse_subscription, format_podcast_list, \
     check_format
from mygpo.podcastlists.views import list_decorator


@csrf_exempt
@require_valid_user
@check_username
@check_format
@never_cache
@allowed_methods(['POST'])
@cors_origin()
def create(request, username, format):
    """ Creates a new podcast list and links to it in the Location header """

    title = request.GET.get('title', None)

    if not title:
        return HttpResponseBadRequest('Title missing')

    slug = slugify(title)

    if not slug:
        return HttpResponseBadRequest('Invalid title')

    plist, created = PodcastList.objects.get_or_create(
        user=request.user,
        slug=slug,
        defaults={
            'id': uuid.uuid1(),
            'title': title,
            'slug': slug,
            'created': datetime.utcnow(),
            'modified': datetime.utcnow(),
        }
    )

    if not created:
        return HttpResponse('List already exists', status=409)

    urls = parse_subscription(request.body.decode('utf-8'), format)
    podcasts = [Podcast.objects.get_or_create_for_url(url) for url in urls]

    for podcast in podcasts:
        plist.add_entry(podcast)

    response = HttpResponse(status=201)
    list_url = reverse('api-get-list', args=[request.user.username, slug, format])
    response['Location'] = list_url

    return response



def _get_list_data(l, username, domain):
    return dict(
            title= l.title,
            name = l.slug,
            web  = 'http://%s%s' % (domain,
                reverse('list-show', args=[username, l.slug])),
        )


@csrf_exempt
@never_cache
@allowed_methods(['GET'])
@cors_origin()
def get_lists(request, username):
    """ Returns a list of all podcast lists by the given user """

    User = get_user_model()
    user = User.objects.get(username=username)
    if not user:
        raise Http404

    lists = PodcastList.objects.filter(user=user)

    site = RequestSite(request)

    get_data = partial(_get_list_data, username=user.username,
                domain=site.domain)
    lists_data = map(get_data, lists)

    return JsonResponse(lists_data)


@csrf_exempt
@check_format
@never_cache
@allowed_methods(['GET', 'PUT', 'DELETE'])
@cors_origin()
def podcast_list(request, username, slug, format):

    handlers = dict(
            GET = get_list,
            PUT = update_list,
            DELETE = delete_list,
        )
    return handlers[request.method](request, username, slug, format)


@list_decorator(must_own=False)
@cors_origin()
def get_list(request, plist, owner, format):
    """ Returns the contents of the podcast list """

    try:
        scale = int(request.GET.get('scale_logo', 64))
    except (TypeError, ValueError):
        return HttpResponseBadRequest('scale_logo has to be a numeric value')

    domain = RequestSite(request).domain
    p_data = lambda p: podcast_data(p, domain, scale)
    title = '{title} by {username}'.format(title=plist.title,
            username=owner.username)

    objs = [entry.content_object for entry in plist.entries.all()]

    return format_podcast_list(objs, format, title, json_map=p_data,
            jsonp_padding=request.GET.get('jsonp', ''),
            xml_template='podcasts.xml', request=request)


@list_decorator(must_own=True)
@cors_origin()
def update_list(request, plist, owner, format):
    """ Replaces the podcasts in the list and returns 204 No Content """
    urls = parse_subscription(request.body.decode('utf-8'), format)
    podcasts = [Podcast.objects.get_or_create_for_url(url) for url in urls]
    plist.set_entries(podcasts)

    return HttpResponse(status=204)


@list_decorator(must_own=True)
@cors_origin()
def delete_list(request, plist, owner, format):
    """ Delete the podcast list and returns 204 No Content """
    plist.delete()
    return HttpResponse(status=204)
