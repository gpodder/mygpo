from django.http import HttpResponse
from django.contrib.auth.models import User
from mygpo.api.opml import Importer, Exporter
from mygpo.api.models import Subscription, Podcast, SubscriptionAction, Device, SUBSCRIBE_ACTION, UNSUBSCRIBE_ACTION
from datetime import datetime
from django.utils.datastructures import MultiValueDictKeyError

LEGACY_DEVICE_NAME = 'Legacy Device'
LEGACY_DEVICE_UID  = 'legacy'

def upload(request):
    try:
        emailaddr = request.POST['username']
        password  = request.POST['password']
        action    = request.POST['action']
        protocol  = request.POST['protocol']
        opml      = request.FILES['opml'].read()
    except MultiValueDictKeyError:
        return HttpResponse("@PROTOERROR", mimetype='text/plain')

    user = auth(emailaddr, password)
    if (not user):
        return HttpResponse('@AUTHFAIL', mimetype='text/plain')

    d, created = Device.objects.get_or_create(user=user, uid=LEGACY_DEVICE_UID,
        defaults = {'type': 'unknown', 'name': LEGACY_DEVICE_NAME})

    existing = Subscription.objects.filter(user=user, device=d)

    existing_urls = [e.podcast.url for e in existing]

    i = Importer(content=opml)
    podcast_urls = [p['url'] for p in i.items]

    new = [item for item in i.items if item['url'] not in existing_urls]
    rem = [e.podcast for e in existing if e.podcast.url not in podcast_urls]

    for n in new:
        p, created = Podcast.objects.get_or_create(url=n['url'], defaults={
                'title' : n['title'],
                'description': n['description'],
                'last_update': datetime.now() })
        s = SubscriptionAction(podcast=p,action=SUBSCRIBE_ACTION, timestamp=datetime.now(), device=d)
        s.save()

    for r in rem:
        s = SubscriptionAction(podcast=r, action=UNSUBSCRIBE_ACTION, timestamp=datetime.now(), device=d)
        s.save()

    return HttpResponse('@SUCCESS', mimetype='text/plain')

def getlist(request):
    emailaddr = request.GET.get('username', None)
    password = request.GET.get('password', None)

    user = auth(emailaddr, password)
    if user is None:
        return HttpResponse('@AUTHFAIL', mimetype='text/plain')

    d, created = Device.objects.get_or_create(user=user, uid=LEGACY_DEVICE_UID,
        defaults = {'type': 'unknown', 'name': LEGACY_DEVICE_NAME})

    podcasts = [s.podcast for s in d.get_subscriptions()]
    exporter = Exporter(filename='')

    opml = exporter.generate(podcasts)

    return HttpResponse(opml, mimetype='text/xml')

def auth(emailaddr, password):
    if emailaddr is None or password is None:
        return None

    try:
        user = User.objects.get(email__exact=emailaddr)
    except User.DoesNotExist:
        return None

    if not user.check_password(password):
        return None

    return user

