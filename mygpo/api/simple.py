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
from mygpo.api.models import Device
from mygpo.api.opml import Exporter, Importer
from mygpo.api.json import JsonResponse
from django.core import serializers

@require_valid_user()
def subscriptions(request, username, device_uid, format):
    
    if request.user.username != username:
        return HttpResponseForbidden()

    if request.method == 'GET':
        return format_subscriptions(get_subscriptions(username, device_uid), format)
        
    elif request.method == 'PUT':
        return set_subscriptions(device_uid, parse_subscription(request.raw_post_data, format))

    else:
        return HttpResponseBadReqest()


def format_subscriptions(subscriptions, format):
    if format == 'txt':
        #return subscriptions formatted as txt
        urls = [p.url for p in subscriptions]
        s = "\n".join(urls)
        return HttpResponse(s, mimetype='text/plain')

    elif format == 'opml':
        # FIXME: We could include the username in the title
        title = 'Your subscription list'
        exporter = Exporter(title)
        opml = exporter.generate(subscriptions)
        return HttpResponse(opml, mimetype='text/xml')

    elif format == 'json':
	json_serializer = serializers.get_serializer("json")()
	p = json_serializer.serialize(subscriptions, ensure_ascii=False, fields=('title', 'description', 'url'))
        return JsonResponse(p)

def get_subscriptions(username, device_uid):
    #get and return subscription list from database (use backend to sync)
    try:
    	d = Device.objects.get(uid=device_uid, user__username=username)
    except Device.DoesNotExist:
	raise Http404
    return [p.podcast for p in d.get_subscriptions()]

def parse_subscription(raw_post_data, format):
    if format == 'txt':
        return []

    elif format == 'opml':
        i = Importer(raw_post_data)
        return i.items

    elif format == 'json':
        #deserialize json
        return []

    else: raise ValueError('unsupported format %s' % format)

def set_subscriptions(device_uid, subscriptions):
    # save subscriptions in database
    pass
