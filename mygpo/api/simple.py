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

import string
from itertools import islice
from functools import wraps

from couchdbkit.exceptions import ResourceNotFound

from django.shortcuts import render
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.sites.models import RequestSite
from django.utils.translation import ugettext as _

from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.api.backend import get_device, BulkSubscribe
from mygpo.core import models
from mygpo.core.models import Podcast
from mygpo.api.opml import Exporter, Importer
from mygpo.api.httpresponse import JsonResponse
from mygpo.directory.toplist import PodcastToplist
from mygpo.directory.models import ExamplePodcasts
from mygpo.api.advanced.directory import podcast_data
from mygpo.directory.search import search_podcasts
from mygpo.decorators import allowed_methods, cors_origin
from mygpo.utils import parse_range, normalize_feed_url
from mygpo.core.json import json, JSONDecodeError
from mygpo.db.couchdb import BulkException
from mygpo.db.couchdb.podcast import podcasts_by_id
from mygpo.db.couchdb.user import suggestions_for_user

import logging
logger = logging.getLogger(__name__)


ALLOWED_FORMATS = ('txt', 'opml', 'json', 'jsonp', 'xml')

def check_format(fn):
    @wraps(fn)
    def tmp(request, format, *args, **kwargs):
        if not format in ALLOWED_FORMATS:
            return HttpResponseBadRequest('Invalid format')

        return fn(request, *args, format=format, **kwargs)
    return tmp


@csrf_exempt
@require_valid_user
@check_username
@check_format
@never_cache
@allowed_methods(['GET', 'PUT', 'POST'])
@cors_origin()
def subscriptions(request, username, device_uid, format):

    user_agent = request.META.get('HTTP_USER_AGENT', '')

    if request.method == 'GET':
        title = _('%(username)s\'s Subscription List') % {'username': username}
        subscriptions = get_subscriptions(request.user, device_uid, user_agent)
        return format_podcast_list(subscriptions, format, title, jsonp_padding=request.GET.get('jsonp'))

    elif request.method in ('PUT', 'POST'):
        try:
            subscriptions = parse_subscription(request.body, format)

        except JSONDecodeError as e:
            return HttpResponseBadRequest('Unable to parse POST data: %s' % str(e))

        return set_subscriptions(subscriptions, request.user, device_uid,
                user_agent)


@csrf_exempt
@require_valid_user
@check_username
@check_format
@never_cache
@allowed_methods(['GET'])
@cors_origin()
def all_subscriptions(request, username, format):

    try:
        scale = int(request.GET.get('scale_logo', 64))
    except (TypeError, ValueError):
        return HttpResponseBadRequest('scale_logo has to be a numeric value')

    if scale not in range(1, 257):
        return HttpResponseBadRequest('scale_logo has to be a number from 1 to 256')


    subscriptions = request.user.get_subscribed_podcasts()
    title = _('%(username)s\'s Subscription List') % {'username': username}
    domain = RequestSite(request).domain
    p_data = lambda p: podcast_data(p, domain, scale)
    return format_podcast_list(subscriptions, format, title,
            json_map=p_data, xml_template='podcasts.xml', request=request)


def format_podcast_list(obj_list, format, title, get_podcast=None,
        json_map=lambda x: x.url, jsonp_padding=None,
        xml_template=None, request=None, template_args={}):
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

    def default_get_podcast(p):
        return p.get_podcast()

    get_podcast = get_podcast or default_get_podcast

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

    elif format == 'jsonp':
        ALLOWED_FUNCNAME = string.letters + string.digits + '_'

        if not jsonp_padding:
            return HttpResponseBadRequest('For a JSONP response, specify the name of the callback function in the jsonp parameter')

        if any(x not in ALLOWED_FUNCNAME for x in jsonp_padding):
            return HttpResponseBadRequest('JSONP padding can only contain the characters %(char)s' % {'char': ALLOWED_FUNCNAME})

        objs = map(json_map, obj_list)
        return JsonResponse(objs, jsonp_padding=jsonp_padding)

    elif format == 'xml':
        if None in (xml_template, request):
            return HttpResponseBadRequest('XML is not a valid format for this request')

        podcasts = map(json_map, obj_list)
        template_args.update({'podcasts': podcasts})

        return render(request, xml_template, template_args,
                content_type='application/xml')

    else:
        return None


def get_subscriptions(user, device_uid, user_agent=None):
    device = get_device(user, device_uid, user_agent)
    return device.get_subscribed_podcasts()


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


    urls = map(normalize_feed_url, urls)
    urls = filter(None, urls)
    urls = set(urls)
    return urls


def set_subscriptions(urls, user, device_uid, user_agent):

    device = get_device(user, device_uid, user_agent, undelete=True)

    subscriptions = dict( (p.url, p) for p in device.get_subscribed_podcasts())
    new = [p for p in urls if p not in subscriptions.keys()]
    rem = [p for p in subscriptions.keys() if p not in urls]

    subscriber = BulkSubscribe(user, device, podcasts=subscriptions)

    for r in rem:
        subscriber.add_action(r, 'unsubscribe')

    for n in new:
        subscriber.add_action(n, 'subscribe')

    try:
        errors = subscriber.execute()
    except BulkException as be:
        for err in be.errors:
            logger.warn('Simple API: %(username)s: Updating subscription for '
                    '%(podcast_url)s on %(device_uid)s failed: '
                    '%(error)s (%(reason)s)'.format(username=user.username,
                        podcast_url=err.doc, device_uid=device.uid,
                        error=err.error, reason=err.reason)
                )

    # Only an empty response is a successful response
    return HttpResponse('', mimetype='text/plain')


@check_format
@allowed_methods(['GET'])
@cache_page(60 * 60)
@cors_origin()
def toplist(request, count, format):
    count = parse_range(count, 1, 100, 100)

    toplist = PodcastToplist()
    entries = toplist[:count]
    domain = RequestSite(request).domain

    try:
        scale = int(request.GET.get('scale_logo', 64))
    except (TypeError, ValueError):
        return HttpResponseBadRequest('scale_logo has to be a numeric value')

    if scale not in range(1, 257):
        return HttpResponseBadRequest('scale_logo has to be a number from 1 to 256')


    def get_podcast(t):
        old_pos, podcast = t
        return podcast.get_podcast()

    def json_map(t):
        old_pos, podcast = t
        podcast.old_pos = old_pos

        p = podcast_data(podcast, domain, scale)
        p.update(dict(
            subscribers           = podcast.subscriber_count(),
            subscribers_last_week = podcast.prev_subscriber_count(),
            position_last_week    = podcast.old_pos,
        ))
        return p

    title = _('gpodder.net - Top %(count)d') % {'count': len(entries)}
    return format_podcast_list(entries,
                               format,
                               title,
                               get_podcast=get_podcast,
                               json_map=json_map,
                               jsonp_padding=request.GET.get('jsonp', ''),
                               xml_template='podcasts.xml',
                               request=request,
                            )


@check_format
@cache_page(60 * 60)
@allowed_methods(['GET'])
@cors_origin()
def search(request, format):

    NUM_RESULTS = 20

    query = request.GET.get('q', '').encode('utf-8')

    try:
        scale = int(request.GET.get('scale_logo', 64))
    except (TypeError, ValueError):
        return HttpResponseBadRequest('scale_logo has to be a numeric value')

    if scale not in range(1, 257):
        return HttpResponseBadRequest('scale_logo has to be a number from 1 to 256')

    if not query:
        return HttpResponseBadRequest('/search.opml|txt|json?q={query}')

    results, total = search_podcasts(q=query, limit=NUM_RESULTS)

    title = _('gpodder.net - Search')
    domain = RequestSite(request).domain
    p_data = lambda p: podcast_data(p, domain, scale)
    return format_podcast_list(results, format, title, json_map=p_data, jsonp_padding=request.GET.get('jsonp', ''), xml_template='podcasts.xml', request=request)


@require_valid_user
@check_format
@never_cache
@allowed_methods(['GET'])
@cors_origin()
def suggestions(request, count, format):
    count = parse_range(count, 1, 100, 100)

    suggestion_obj = suggestions_for_user(request.user)
    suggestions = suggestion_obj.get_podcasts(count)
    title = _('gpodder.net - %(count)d Suggestions') % {'count': len(suggestions)}
    domain = RequestSite(request).domain
    p_data = lambda p: podcast_data(p, domain)
    return format_podcast_list(suggestions, format, title, json_map=p_data, jsonp_padding=request.GET.get('jsonp'))


@check_format
@allowed_methods(['GET'])
@cache_page(60 * 60)
@cors_origin()
def example_podcasts(request, format):

    podcasts = cache.get('example-podcasts', None)

    try:
        scale = int(request.GET.get('scale_logo', 64))
    except (TypeError, ValueError):
        return HttpResponseBadRequest('scale_logo has to be a numeric value')

    if scale not in range(1, 257):
        return HttpResponseBadRequest('scale_logo has to be a number from 1 to 256')


    if not podcasts:

        try:
            examples = ExamplePodcasts.get('example_podcasts')
            ids = examples.podcast_ids
            podcasts = podcasts_by_id(ids)
            cache.set('example-podcasts', podcasts)

        except ResourceNotFound:
            podcasts = []

    title = 'gPodder Podcast Directory'
    domain = RequestSite(request).domain
    p_data = lambda p: podcast_data(p, domain, scale)
    return format_podcast_list(
            podcasts,
            format,
            title,
            json_map=p_data,
            xml_template='podcasts.xml',
            request=request,
        )
