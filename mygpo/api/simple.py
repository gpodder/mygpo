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
from mygpo.api.models import Device, SubscriptionAction, Podcast, SUBSCRIBE_ACTION, UNSUBSCRIBE_ACTION
from mygpo.api.opml import Exporter, Importer
from mygpo.api.json import JsonResponse
from django.core import serializers
from datetime import datetime
from mygpo.api.httpresponse import HttpResponseNotAuthorized
import re

@require_valid_user()
def subscriptions(request, username, device_uid, format):
    
    if request.user.username != username:
        #throw 401
        return HttpResponseNotAuthorized()

    if request.method == 'GET':
        return format_subscriptions(get_subscriptions(request.user, device_uid), format, username)
        
    elif request.method == 'PUT':
        return set_subscriptions(parse_subscription(request.raw_post_data, format, request.user, device_uid))
    else:
        return HttpResponseBadReqest()


def format_subscriptions(subscriptions, format, username):
    if format == 'txt':
        #return subscriptions formatted as txt
        urls = [p.url for p in subscriptions]
        s = "\n".join(urls)
        s += "\n"
        return HttpResponse(s, mimetype='text/plain')

    elif format == 'opml':
        title = username + '\'s subscription list'
        exporter = Exporter(title)
        opml = exporter.generate(subscriptions)
        return HttpResponse(opml, mimetype='text/xml')

    elif format == 'json':
        urls = [p.url for p in subscriptions]
        return JsonResponse(urls)

def get_subscriptions(user, device_uid):
    #get and return subscription list from database (use backend to sync)
    try:
        d = Device.objects.get(uid=device_uid, user=user)
    except Device.DoesNotExist:
        raise Http404('Device doesn\'t exist!')
    return [p.podcast for p in d.get_subscriptions()]

def parse_subscription(raw_post_data, format, user, device_uid):
    if format == 'txt':
        sub = raw_post_data.split('\n')
        urls = [x for x in sub if x != '\r']

    elif format == 'opml':
        i = Importer(content=raw_post_data)
        urls = [p['url'] for p in i.items]

    elif format == 'json':
        sub = raw_post_data.split('"')
        pattern = '^[a-zA-z]'
        urls = [x for x in sub if re.search(pattern, x) != None]

    else: raise ValueError('unsupported format %s' % format)
    
    d, created = Device.objects.get_or_create(user=user, uid=device_uid, 
                defaults = {'type': 'other', 'name': 'unknown_' + device_uid})
    
    podcasts = [p.podcast for p in d.get_subscriptions()]
    old = [p.url for p in podcasts]    
    new = [p for p in urls if p not in old]
    rem = [p for p in old if p not in urls]
    
    return new, rem, d


def set_subscriptions(subscriptions):
    new, rem, d = subscriptions
    
    if new != []:
        for n in new:
            p, created = Podcast.objects.get_or_create(url=n,
                        defaults={'title':n,'description':n,'last_update':datetime.now()})
            s = SubscriptionAction(podcast=p, action=SUBSCRIBE_ACTION, device=d)
            s.save()
    
    if rem != []: 
        for r in rem:
            p = Podcast.objects.get(url=r)
            s = SubscriptionAction(podcast=p, action=UNSUBSCRIBE_ACTION, device=d)
            s.save()
	
    return HttpResponse('Success', mimetype='text/plain')

