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

from itertools import islice
from mygpo.api.basic_auth import require_valid_user, check_username
from django.http import HttpResponse, HttpResponseBadRequest
from mygpo.core.models import Suggestions
from mygpo.api.models import Device, Podcast
from mygpo.api.opml import Exporter, Importer
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.sanitizing import sanitize_url
from mygpo.api.backend import get_toplist, get_all_subscriptions
from mygpo.api.advanced.directory import podcast_data
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from mygpo.search.models import SearchEntry
from django.utils.translation import ugettext as _
from mygpo.decorators import allowed_methods
from mygpo.migrate import use_couchdb


try:
    import json

    # Python 2.5 seems to have a different json module
    if not 'dumps' in dir(json):
        raise ImportError

except ImportError:
    import simplejson as json


ALLOWED_FORMATS = ('txt', 'opml', 'json')

def check_format(fn):
    def tmp(request, format, *args, **kwargs):
        if not format in ALLOWED_FORMATS:
            return HttpResponseBadRequest('Invalid format')

        return fn(request, *args, format=format, **kwargs)
    return tmp


@csrf_exempt
@require_valid_user
@check_username
@check_format
@allowed_methods(['GET', 'PUT', 'POST'])
def subscriptions(request, username, device_uid, format):

    if request.method == 'GET':
        title = _('%(username)s\'s Subscription List') % {'username': username}
        subscriptions = get_subscriptions(request.user, device_uid)
        return format_podcast_list(subscriptions, format, title)

    elif request.method in ('PUT', 'POST'):
        subscriptions = parse_subscription(request.raw_post_data, format)
        return set_subscriptions(subscriptions, request.user, device_uid)


@csrf_exempt
@require_valid_user
@check_username
@check_format
@allowed_methods(['GET'])
def all_subscriptions(request, username, format):
    subscriptions = get_all_subscriptions(request.user)
    title = _('%(username)s\'s Subscription List') % {'username': username}
    return format_podcast_list(subscriptions, format, title)


def format_podcast_list(obj_list, format, title, get_podcast=lambda x: x, json_map=lambda x: x.url):
    """
    Formats a list of podcasts for use in a API response

    obj_list is a list of podcasts or objects that contain podcasts
    format is one if txt, opml or json
    title is a label of the list
    if obj_list is a list of objects containing podcasts, get_podcast is the
      function used to get the podcast out of the each of these objects
    json_map is a function returning the contents of an object (from obj_list)
      that should be contained in the result (only used for format='json')
    """
    if format == 'txt':
        podcasts = map(get_podcast, obj_list)
        s = '\n'.join([p.url for p in podcasts] + [''])
        return HttpResponse(s, mimetype='text/plain')

    elif format == 'opml':
        podcasts = map(get_podcast, obj_list)
        exporter = Exporter(title)
        opml = exporter.generate(podcasts)
        return HttpResponse(opml, mimetype='text/xml')

    elif format == 'json':
        objs = map(json_map, obj_list)
        return JsonResponse(objs)

    else:
        return None


def get_subscriptions(user, device_uid):
    device = get_object_or_404(Device, uid=device_uid, user=user, deleted=False)

    subscriptions = sorted(device.get_subscriptions(), \
        key=lambda s: s.subscribed_since, reverse=True)

    return [s.podcast for s in subscriptions]


def parse_subscription(raw_post_data, format):
    if format == 'txt':
        urls = raw_post_data.split('\n')

    elif format == 'opml':
        begin = raw_post_data.find('<?xml')
        end = raw_post_data.find('</opml>') + 7
        i = Importer(content=raw_post_data[begin:end])
        urls = [p['url'] for p in i.items]

    elif format == 'json':
        begin = raw_post_data.find('[')
        end = raw_post_data.find(']') + 1
        urls = json.loads(raw_post_data[begin:end])

    else:
        return []

    urls = map(sanitize_url, urls)
    urls = filter(lambda x: x, urls)
    urls = set(urls)
    return urls


def set_subscriptions(urls, user, device_uid):
    device, created = Device.objects.get_or_create(user=user, uid=device_uid)

    # undelete a previously deleted device
    if device.deleted:
        device.deleted = False
        device.save()

    old = [s.podcast.url for s in device.get_subscriptions()]
    new = [p for p in urls if p not in old]
    rem = [p for p in old if p not in urls]

    for r in rem:
        p = Podcast.objects.get(url=r)
        p.unsubscribe(device)

    for n in new:
        p, created = Podcast.objects.get_or_create(url=n)
        p.subscribe(device)

    # Only an empty response is a successful response
    return HttpResponse('', mimetype='text/plain')


@check_format
@allowed_methods(['GET'])
def toplist(request, count, format):
    if int(count) not in range(1,100):
        count = 100

    toplist = get_toplist(count)

    def json_map(t):
        p = podcast_data(t.get_podcast())
        p.update(dict(
            subscribers=           t.subscriptions,
            subscribers_last_week= t.oldplace,
            position_last_week=    t.oldplace
        ))
        return p

    title = _('gpodder.net - Top %(count)d') % {'count': len(toplist)}
    return format_podcast_list(toplist,
                               format,
                               title,
                               get_podcast=lambda x: x.get_podcast(),
                               json_map=json_map)


@check_format
@allowed_methods(['GET'])
def search(request, format):
    query = request.GET.get('q', '').encode('utf-8')

    if not query:
        return HttpResponseBadRequest('/search.opml|txt|json?q={query}')

    results = [r.get_podcast() for r in SearchEntry.objects.search(query)[:20]]

    title = _('gpodder.net - Search')
    return format_podcast_list(results, format, title, json_map=podcast_data)


@require_valid_user
@check_format
@allowed_methods(['GET'])
@use_couchdb()
def suggestions(request, count, format):
    count = int(count)
    if count not in range(1,100):
        count = 100

    suggestion_obj = Suggestions.for_user_oldid(request.user.id)
    suggestions = [p.get_old_obj() for p in islice(suggestion_obj.get_podcasts(), count)]
    title = _('gpodder.net - %(count)d Suggestions') % {'count': len(suggestions)}
    return format_podcast_list(suggestions, format, title, json_map=podcast_data)


