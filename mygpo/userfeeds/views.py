from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from mygpo.userfeeds.auth import require_token_auth
from mygpo.userfeeds.feeds import FavoriteFeed

@require_token_auth('fav-feed', 'r')
def favorite_feed(request, username):

    site = Site.objects.get_current()
    user = get_object_or_404(User, username=username)
    feed = FavoriteFeed(user)

    return render_to_response('userfeed.xml', {
        'site': site,
        'feed_user': user,
        'feed': feed,
        }, context_instance=RequestContext(request), mimetype='text/xml')

