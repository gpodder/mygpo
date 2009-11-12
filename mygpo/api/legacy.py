from django.http import HttpResponse
from mygpo.api.opml import Importer, Exporter
from mygpo.api.models import Subscription, Podcast, UserAccount, SubscriptionAction, Device
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
        return HttpResponse("@PROTOERROR")

    user = auth(emailaddr, password)
    if (not user):
        return HttpResponse('@AUTHFAIL')

    existing = Subscription.objects.filter(user__email__exact=emailaddr)

    existing_urls = [e.podcast.url for e in existing]

    i = Importer(content=opml)
    podcast_urls = [p['url'] for p in i.items]

    new = [item for item in i.items if item['url'] not in existing_urls]
    rem = [e.podcast for e in existing if e.podcast.url not in podcast_urls]

    d, created = Device.objects.get_or_create(user=user, uid=LEGACY_DEVICE_UID,
            defaults = {'type': 'unknown', 'name': LEGACY_DEVICE_NAME})

    for n in new:
        p, created = Podcast.objects.get_or_create(url=n['url'], defaults={
                'title' : n['title'],
                'description': n['description'],
                'last_update': datetime.now() })
        s = SubscriptionAction(podcast=p,action='subscribe', timestamp=datetime.now(), device=d)
        s.save()

    for r in rem:
        s = SubscriptionAction(podcast=r, action='unsubscribe', timestamp=datetime.now(), device=d)
        s.save()

    return HttpResponse('@SUCCESS')

def getlist(request):
    emailaddr = request.GET.get('username', None)
    password = request.GET.get('password', None)

    user = auth(emailaddr, password)
    if user is None:
        return HttpResponse('@AUTHFAIL')

    podcasts = [s.podcast for s in Subscription.objects.filter(user=user)]
    exporter = Exporter(filename='')

    opml = exporter.generate(podcasts)

    return HttpResponse(opml)

def auth(emailaddr, password):
    if emailaddr is None or password is None:
        return None

    try:
        user = UserAccount.objects.get(email__exact=emailaddr)
    except UserAccount.DoesNotExist:
        return None

    if not user.check_password(password):
        return None
    
    return user

