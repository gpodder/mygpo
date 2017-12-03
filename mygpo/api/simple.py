import json
import string
from itertools import islice
from functools import wraps

from django.shortcuts import render
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.contrib.sites.requests import RequestSite
from django.utils.translation import ugettext as _

from mygpo.api.basic_auth import require_valid_user, check_username
from mygpo.api.backend import get_device
from mygpo.podcasts.models import Podcast
from mygpo.api.opml import Exporter, Importer
from mygpo.api.httpresponse import JsonResponse
from mygpo.directory.models import ExamplePodcast
from mygpo.api.advanced.directory import podcast_data
from mygpo.subscriptions import get_subscribed_podcasts, subscribe, unsubscribe
from mygpo.directory.search import search_podcasts
from mygpo.decorators import allowed_methods, cors_origin
from mygpo.utils import parse_range, normalize_feed_url

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
            body = request.body.decode('utf-8')
            subscriptions = parse_subscription(body, format)

        except ValueError as e:
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


    subscriptions = get_subscribed_podcasts(request.user)
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
        return p

    get_podcast = get_podcast or default_get_podcast

    if format == 'txt':
        podcasts = map(get_podcast, obj_list)
        s = '\n'.join([p.url for p in podcasts] + [''])
        return HttpResponse(s, content_type='text/plain')

    elif format == 'opml':
        podcasts = map(get_podcast, obj_list)
        exporter = Exporter(title)
        opml = exporter.generate(podcasts)
        return HttpResponse(opml, content_type='text/xml')

    elif format == 'json':
        objs = list(map(json_map, obj_list))
        return JsonResponse(objs)

    elif format == 'jsonp':
        ALLOWED_FUNCNAME = string.ascii_letters + string.digits + '_'

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
    """ Parses the data according to the format """
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

    urls = filter(None, urls)
    urls = list(map(normalize_feed_url, urls))
    return urls


def set_subscriptions(urls, user, device_uid, user_agent):

    # remove empty urls
    urls = list(filter(None, (u.strip() for u in urls)))

    device = get_device(user, device_uid, user_agent, undelete=True)

    subscriptions = dict( (p.url, p) for p in device.get_subscribed_podcasts())
    new = [p for p in urls if p not in subscriptions.keys()]
    rem = [p for p in subscriptions.keys() if p not in urls]

    remove_podcasts = Podcast.objects.filter(urls__url__in=rem)
    for podcast in remove_podcasts:
        unsubscribe(podcast, user, device)

    for url in new:
        podcast = Podcast.objects.get_or_create_for_url(url).object
        subscribe(podcast, user, device, url)

    # Only an empty response is a successful response
    return HttpResponse('', content_type='text/plain')


@check_format
@allowed_methods(['GET'])
@cache_page(60 * 60)
@cors_origin()
def toplist(request, count, format):
    count = parse_range(count, 1, 100, 100)

    entries = Podcast.objects.all().toplist()[:count]
    domain = RequestSite(request).domain

    try:
        scale = int(request.GET.get('scale_logo', 64))
    except (TypeError, ValueError):
        return HttpResponseBadRequest('scale_logo has to be a numeric value')

    if scale not in range(1, 257):
        return HttpResponseBadRequest('scale_logo has to be a number from 1 to 256')


    def get_podcast(t):
        return t

    def json_map(t):
        podcast = t
        p = podcast_data(podcast, domain, scale)
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

    query = request.GET.get('q', '')

    try:
        scale = int(request.GET.get('scale_logo', 64))
    except (TypeError, ValueError):
        return HttpResponseBadRequest('scale_logo has to be a numeric value')

    if scale not in range(1, 257):
        return HttpResponseBadRequest('scale_logo has to be a number from 1 to 256')

    if not query:
        return HttpResponseBadRequest('/search.opml|txt|json?q={query}')

    results = search_podcasts(query)[:NUM_RESULTS]

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

    user = request.user
    suggestions = Podcast.objects.filter(podcastsuggestion__suggested_to=user,
                                         podcastsuggestion__deleted=False)
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
        podcasts = list(ExamplePodcast.objects.get_podcasts())
        cache.set('example-podcasts', podcasts)

    podcast_ad = Podcast.objects.get_advertised_podcast()
    if podcast_ad:
        podcasts = [podcast_ad] + podcasts

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
