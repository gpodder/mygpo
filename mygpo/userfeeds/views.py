from django.shortcuts import render, get_object_or_404
from django.contrib.sites.models import RequestSite
from django.contrib.auth import get_user_model
from django.http import Http404

from mygpo.userfeeds.auth import require_token_auth
from mygpo.userfeeds.feeds import FavoriteFeed


@require_token_auth('favorite_feeds_token')
def favorite_feed(request, username):

    site = RequestSite(request)

    User = get_user_model()
    user = get_object_or_404(User, username=username)

    feed = FavoriteFeed(user)

    return render(request, 'userfeed.xml', {
        'site': site,
        'feed_user': user,
        'feed': feed,
        }, content_type='text/xml')
