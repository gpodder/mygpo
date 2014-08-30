from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.sites.models import RequestSite
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control

from mygpo.suggestions.tasks import update_suggestions
from mygpo.db.couchdb.user import (suggestions_for_user,
    blacklist_suggested_podcast)


@never_cache
@login_required
def blacklist(request, blacklisted_podcast):
    user = request.user
    suggestion = suggestions_for_user(user)
    blacklist_suggested_podcast(suggestion, blacklisted_podcast.get_id())
    update_suggestions.delay(user)
    return HttpResponseRedirect(reverse('suggestions'))


@never_cache
@login_required
def rate_suggestions(request):
    rating_val = int(request.GET.get('rate', None))

    suggestion = suggestions_for_user(request.user)
    suggestion.rate(rating_val, request.user.profile.uuid.hex)
    suggestion.save()

    messages.success(request, _('Thanks for rating!'))

    return HttpResponseRedirect(reverse('suggestions'))

@vary_on_cookie
@cache_control(private=True)
@login_required
def suggestions(request):
    suggestion_obj = suggestions_for_user(request.user)
    suggestions = suggestion_obj.get_podcasts()
    current_site = RequestSite(request)
    return render(request, 'suggestions.html', {
        'entries': suggestions,
        'url': current_site
    })
