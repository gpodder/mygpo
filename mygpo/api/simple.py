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

from mygpo.api.basic_auth import require_valid_user
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404
from mygpo.api.models import Device, SubscriptionAction, Podcast, SUBSCRIBE_ACTION, UNSUBSCRIBE_ACTION, ToplistEntry, SuggestionEntry
from mygpo.api.opml import Exporter, Importer
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.sanitizing import sanitize_url
from django.core import serializers
from datetime import datetime
from mygpo.api.httpresponse import HttpErrorResponse
import re
from mygpo.log import log
from haystack.query import SearchQuerySet
from django.views.decorators.csrf import csrf_exempt

try:
    import json

    # Python 2.5 seems to have a different json module
    if not 'dumps' in dir(json):
        raise ImportError

except ImportError:
    import json

@csrf_exempt
@require_valid_user
def subscriptions(request, username, device_uid, format):
    
    if request.user.username != username:
        return HttpErrorResponse(401, 'Invalid user')

    if request.method == 'GET':
        return format_subscriptions(get_subscriptions(request.user, device_uid), format, username)
        
    elif request.method in ('PUT', 'POST'):
        return set_subscriptions(parse_subscription(request.raw_post_data, format, request.user, device_uid))
    
    else:
        return HttpResponseBadRequest()


def format_subscriptions(subscriptions, format, username):
    if subscriptions == 404:
        return HttpErrorResponse(404, 'Invalid device ID')

    if format == 'txt':
        #return subscriptions formatted as txt
        urls = [p.url for p in subscriptions]
        s = '\n'.join(urls)
        s += '\n'
        return HttpResponse(s, mimetype='text/plain')

    elif format == 'opml':
        title = username + '\'s subscription list'
        exporter = Exporter(title)
        opml = exporter.generate(subscriptions)
        return HttpResponse(opml, mimetype='text/xml')

    elif format == 'json':
        urls = [p.url for p in subscriptions]
        return JsonResponse(urls)
        
    else: 
        return HttpResponseBadRequest('Invalid format')


def get_subscriptions(user, device_uid):
    #get and return subscription list from database (use backend to sync)
    try:
        d = Device.objects.get(uid=device_uid, user=user, deleted=False)

    except Device.DoesNotExist:
        raise Http404

    return [p.podcast for p in d.get_subscriptions()]

def parse_subscription(raw_post_data, format, user, device_uid):
    format_ok = True
    if format == 'txt':
        sub = raw_post_data.split('\n')
        p = '^http'
        urls = []
        for x in sub:
            if re.search(p, x) == None:
                log('parse_subscription (txt): invalid podcast url: %s' % x)
            else:
                urls.append(x)

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
        urls = []
        format_ok = False

    urls_sanitized = []
    for u in urls:
        us = sanitize_url(u)
        if us != '': urls_sanitized.append(us)
    
    d, created = Device.objects.get_or_create(user=user, uid=device_uid, 
                defaults = {'type': 'other', 'name': device_uid})

    # undelete a previously deleted device
    if d.deleted:
        d.deleted = False
        d.save()

    podcasts = [p.podcast for p in d.get_subscriptions()]
    old = [p.url for p in podcasts]    
    new = [p for p in urls_sanitized if p not in old]
    rem = [p for p in old if p not in urls_sanitized]

    return format_ok, new, rem, d


def set_subscriptions(subscriptions):
    format_ok, new, rem, d = subscriptions
    
    if format_ok == False:
        return HttpResponseBadRequest('Invalid format') 
    
    for r in rem:
        p = Podcast.objects.get(url=r)
        s = SubscriptionAction(podcast=p, device=d, action=UNSUBSCRIBE_ACTION)
        s.save()
    
    for n in new:
        p, created = Podcast.objects.get_or_create(url=n,
            defaults={'title':n,'description':n,'last_update':datetime.now()})
        s = SubscriptionAction(podcast=p, action=SUBSCRIBE_ACTION, device=d)
        s.save()

    # Only an empty response is a successful response
    return HttpResponse('', mimetype='text/plain')

#get toplist
def toplist(request, count, format):
    if request.method == 'GET':
        if int(count) not in range(1,100):
            count = 100
        return format_toplist(get_toplist(count), count, format)
    else:
        return HttpResponseBadRequest('Invalid request')


def get_toplist(count):        
    return ToplistEntry.objects.all().order_by('-subscriptions')[:int(count)]


def format_toplist(toplist, count, format): 
    if format == 'txt':
        urls = [p.get_podcast().url for p in toplist]
        s = '\n'.join(urls)
        s += '\n'
        return HttpResponse(s, mimetype='text/plain')

    elif format == 'opml':
        exporter = Exporter('my.gpodder.org - Top %s' % count)
        opml = exporter.generate([t.get_podcast() for t in toplist])
        return HttpResponse(opml, mimetype='text/xml')

    elif format == 'json':
        json = [{'url':t.get_podcast().url, 'title':t.get_podcast().title,'description':t.get_podcast().description, 'subscribers':t.subscriptions, 'subscribers_last_week':t.oldplace} for t in toplist]
        return JsonResponse(json)
        
    else: 
        return HttpResponseBadRequest('Invalid format')

#get search 
def search(request, format):
    if request.method == 'GET':
        query = request.GET.get('q')
        
        if query == None:
            return HttpErrorResponse(404, '/search.opml|txt|json?q={query}')
        
        return format_results(get_results(query), format)
    else:
        return HttpResponseBadRequest('Invalid request')
        
        
def get_results(query):
    search = SearchQuerySet().filter(content=query).models(Podcast)
    results = []
    for r in search:
        p = Podcast.objects.get(pk=r.pk)
        results.append(p)
        
    return results
    
    
def format_results(results, format):
    if format == 'txt':
        urls = [r.url for r in results]
        s = '\n'.join(urls)
        s += '\n'
        return HttpResponse(s, mimetype='text/plain')

    elif format == 'opml':
        exporter = Exporter('my.gpodder.org - Search')
        opml = exporter.generate(results)
        return HttpResponse(opml, mimetype='text/xml')

    elif format == 'json':
        json = [{'url':p.url, 'title':p.title, 'description':p.description} for p in results]
        return JsonResponse(json)
        
    else: 
        return HttpResponseBadRequest('Invalid format')
       
#get suggestions
@require_valid_user
def suggestions(request, count, format):
    if request.method == 'GET':
        if int(count) not in range(1,100):
            count = 100
        return format_suggestions(get_suggestions(request.user, count), count, format)
    else:
        return HttpResponseBadRequest('Invalid request')
        
def get_suggestions(user, count):
    suggestions = SuggestionEntry.forUser(user)[:int(count)]
    return [s.podcast for s in suggestions]
    
def format_suggestions(suggestions, count, format):
    if format == 'txt':
        urls = [s.url for s in suggestions]
        s = '\n'.join(urls)
        s += '\n'
        return HttpResponse(s, mimetype='text/plain')

    elif format == 'opml':
        exporter = Exporter('my.gpodder.org - %s Suggestions' % count)
        opml = exporter.generate(suggestions)
        return HttpResponse(opml, mimetype='text/xml')

    elif format == 'json':
        json = [{'url':p.url, 'title':p.title, 'description':p.description} for p in suggestions]
        return JsonResponse(json)
        
    else: 
        return HttpResponseBadRequest('Invalid format')
        
