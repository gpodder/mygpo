from mygpo.api.basic_auth import require_valid_user
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, Http404
from mygpo.api.models import Device, SubscriptionAction
from mygpo.api.opml import Exporter
from mygpo.api.json import JsonResponse
from django.core import serializers

@require_valid_user()
def subscriptions(request, username, device_uid, format):
    
    if request.user.username != username:
        return HttpResponseForbidden()

    if request.method == 'GET':
        return format_subscriptions(get_subscriptions(username, device_uid), format)
        
    elif request.method == 'PUT':
        return set_subscriptions(parse_subscription(request.raw_post_data, format, username, device_uid))

    else:
        return HttpResponseBadReqest()


def format_subscriptions(subscriptions, format):
    if format == 'txt':
        #return subscriptions formatted as txt
        urls = [p.url for p in subscriptions]
        s = "\n".join(urls)
        return HttpResponse(s, mimetype='text/plain')

    elif format == 'opml':
        return HttpResponse(Exporter().generate(subscriptions), mimetype='text/xml')
    
    elif format == 'json':
	json_serializer = serializers.get_serializer("json")()
	p = json_serializer.serialize(subscriptions, fields=('title', 'description', 'url'))
        return JsonResponse(p)

def get_subscriptions(username, device_uid):
    #get and return subscription list from database (use backend to sync)
    try:
    	d = Device.objects.get(uid=device_uid, user__username=username)
    except Device.DoesNotExist:
	raise Http404
    return [p.podcast for p in d.get_subscriptions()]

def parse_subscription(raw_post_data, format, username, device_uid):
    if format == 'txt':
	urls = []

    elif format == 'opml':
        i = Importer(content=raw_post_data)
	urls = [p['url'] for p in i.items]

    elif format == 'json':
        #deserialize json
        urls = []

    else: raise ValueError('unsupported format %s' % format)

    old = [p.url for p in get_subscriptions(username, device_uid)]
    new = [p for p in urls if urls not in old]
    rem = [p for p in old if old not in urls]
    return new, rem, username, device_uid


def set_subscriptions(subscriptions):
    new = subscriptions[0]
    rem = subscriptions[1]

    d, created = Device.objects.get_or_create(uid=subscriptions[2], user__username=subscriptions[3])

    for r in rem:
	s=SubscriptionAction(podcast=r, action='unsubscribe', timestamp=datetime.now(), device=d)
	s.save()
	
    for n in new:
	 p, created = Podcast.objects.get_or_create(url=n['url'], defaults={
                'title' : n['title'],
                'description': n['description'],
                'last_update': datetime.now() })

	s=SubscriptionAction(podcast=p, action='subscribe', timestamp=datetime.now(), device=d)
        s.save()

    return HttpResponse('Success', mimetype='text/plain#)

