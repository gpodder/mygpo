from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.sites.requests import RequestSite
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control

from mygpo.podcasts.views.podcast import slug_decorator, id_decorator
from mygpo.suggestions.models import PodcastSuggestion
from mygpo.podcasts.models import Podcast

import logging
logger = logging.getLogger(__name__)


@never_cache
@login_required
def blacklist(request, blacklisted_podcast):
    user = request.user

    logger.info('Removing suggestion of "{podcast}" for "{user}"'.format(
        podcast=blacklisted_podcast, user=user))

    suggestion = PodcastSuggestion.objects.filter(suggested_to=user,
                                                  podcast=blacklisted_podcast)\
                                          .update(deleted=True)
    return HttpResponseRedirect(reverse('suggestions'))


@vary_on_cookie
@cache_control(private=True)
@login_required
def suggestions(request):
    user = request.user
    suggestions = Podcast.objects.filter(podcastsuggestion__suggested_to=user,
                                         podcastsuggestion__deleted=False)
    current_site = RequestSite(request)
    return render(request, 'suggestions.html', {
        'entries': suggestions,
        'url': current_site
    })


blacklist_slug = slug_decorator(blacklist)
blacklist_id = id_decorator(blacklist)
