from mygpo.api.basic_auth import logged_in_or_basicauth
from django.http import HttpResponse

@logged_in_or_basicauth('my.gpodder.org - Simple API')
def all_subscriptions(request, username, format):
    return HttpResponse()

@logged_in_or_basicauth
def device_subscription(request, username, device, format):
    return HttpResponse()

