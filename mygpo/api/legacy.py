from django.http import HttpResponse
from mygpo.api.opml import Importer
from mygpo.api.models import Subscription, Podcast, UserAccount

def upload(request):
    emailaddr = request.GET['username']
    action    = request.GET['action']
    protocol  = request.GET['protocol']
    opml_file = request.FILES['opml']
    opml      = opml_file.read()
    
    if (not auth(request)):
        return HttpResponse('@AUTHFAIL')

    try:
        existing = Subscription.objects.get(user__email__exact=emailaddr)
    except Subscription.DoesNotExist:
        existing = []

    print existing

    existing_urls = [e.podcast.url for e in existing]

    print existing_urls
    
    i = Importer(content=request.raw_post_data)
    podcasts = i.items

    new = [item for item in i.items if item['url'] not in existing_urls]
    rem = [e.podcast for e in existing if e.podcast.url not in i.items]

    print new
    print rem

    for n in new:
        try:
            p = Podcast.objects.get(url__exact=n['url'])
        except Podcast.DoesNotExist:
            p = Podcast(url=n['url'])
            p.save()
        s = SubscriptionAction(podcast=p,action='subscribe', timestamp=now())
        s.save()

    for p in rem:
        s = SubscriptionAction(podcast=p, action='unsubscribe', timestamp=now())
        s.save()

    return HttpResponse('@SUCCESS')

def getlist(request):
    if (not auth(request)):
        return HttpResponse('@AUTHFAIL')

    # build and send list


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

