from mygpo.api.basic_auth import require_valid_user
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden

@require_valid_user()
def subscriptions(request, username, device, format):
    
    if request.user.username != username:
        return HttpResponseForbidden()

    if request.method == 'GET':
        return format_subscriptions(get_subscriptions(device), format)
        
    elif request.method == 'PUT':
        return set_subscriptions(device, parse_subscription(request.raw_post_data, format))

    else:
        return HttpResponseBadReqest()


def format_subscriptions(subscriptions, format):
    if format == 'txt':
        #return subscriptions formatted as txt
        return HttpRequest('', mimetype='text/plain')

    elif format == 'opml':
        e = Exporter(subscriptions)
        return HttpRequest(e.generate(), mimetype='text/xml')
    
    elif format == 'json':
        return JsonRequest(subscriptions)

def get_subscriptions(device):
    # get and return subscription list from database (use backend to sync)
    return []

def parse_subscription(raw_post_data, format):
    if format == 'txt':
        return []

    elif format == 'opml':
        i = Importer(content=raw_post_data)
        return i.items

    elif format == 'json':
        #deserialize json
        return []

    else: raise ValueError('unsupported format %s' % format)

def set_subscriptions(device, subscriptions):
    # save subscriptions in database
    pass
