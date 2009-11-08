from django.http import HttpResponse
from mygpo.api.opml import Importer, Exporter
from mygpo.api.models import Subscription, Podcast, UserAccount, SubscriptionAction, Device
from datetime import datetime
from django.utils.datastructures import MultiValueDictKeyError

LEGACY_DEVICE='Legacy Device'

def upload(request):
    try:
        emailaddr = request.GET['username']
        action    = request.GET['action']
        protocol  = request.GET['protocol']
        opml      = request.FILES['opml'].read()
    except MultiValueDictKeyError:
        return HttpResponse("@PROTOERROR")

    user = auth(request)
    if (not user):
        return HttpResponse('@AUTHFAIL')

    existing = Subscription.objects.filter(user__email__exact=emailaddr)

    existing_urls = [e.podcast.url for e in existing]

    i = Importer(content=opml)
    podcast_urls = [p['url'] for p in i.items]

    new = [item for item in i.items if item['url'] not in existing_urls]
    rem = [e.podcast for e in existing if e.podcast.url not in podcast_urls]

    d, created = Device.objects.get_or_create(user=user, name__exact=LEGACY_DEVICE, defaults={'type': 'other'})

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

    user = auth(request)
    if (not user):
        return HttpResponse('@AUTHFAIL')

    podcasts = [s.podcast for s in Subscription.objects.filter(user=user)]
    exporter = Exporter(filename='')

    opml = exporter.generate(podcasts)

    return HttpResponse(opml)

def auth(request):
    emailaddr = request.GET['username']
    password  = request.GET['password']

    try:
        user = UserAccount.objects.get(email__exact=emailaddr)
    except UserAccount.DoesNotExist:
        return False

    if not user.check_password(password):
        return False
    
    return user

