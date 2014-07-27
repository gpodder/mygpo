#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

import sys
from collections import defaultdict
from datetime import datetime, timedelta

try:
    import gevent
except ImportError:
    gevent = None

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.sites.models import RequestSite
from django.views.generic.base import View
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control

from mygpo.decorators import repeat_on_conflict
from mygpo.podcasts.models import Podcast, Episode
from mygpo.users.models import History, HistoryEntry, Client
from mygpo.users.tasks import update_suggestions
from mygpo.users.subscriptions import get_subscribed_podcasts
from mygpo.web.utils import process_lang_params
from mygpo.utils import parse_range
#from mygpo.web.views.podcast import slug_id_decorator
from mygpo.users.settings import FLATTR_AUTO, FLATTR_TOKEN
from mygpo.publisher.models import PublishedPodcast
from mygpo.db.couchdb.episode_state import favorite_episode_ids_for_user
from mygpo.db.couchdb.user import (suggestions_for_user,
    blacklist_suggested_podcast)
from mygpo.db.couchdb.directory import tags_for_user
from mygpo.db.couchdb.podcastlist import podcastlists_for_user


@vary_on_cookie
@cache_control(private=True)
def home(request):
    if request.user.is_authenticated():
        return dashboard(request)
    else:
        return welcome(request)


@vary_on_cookie
@cache_control(private=True)
def welcome(request):
    current_site = RequestSite(request)

    lang = process_lang_params(request)

    toplist = Podcast.objects.all().toplist(lang)

    return render(request, 'home.html', {
          'url': current_site,
          'toplist': toplist,
    })


@vary_on_cookie
@cache_control(private=True)
@login_required
def dashboard(request, episode_count=10):

    subscribed_podcasts = list(get_subscribed_podcasts(request.user))
    site = RequestSite(request)

    checklist = []

    if request.user.client_set.count():
        checklist.append('devices')

    if subscribed_podcasts:
        checklist.append('subscriptions')

    if favorite_episode_ids_for_user(request.user):
        checklist.append('favorites')

    if not request.user.profile.get_token('subscriptions_token'):
        checklist.append('share')

    if not request.user.profile.get_token('favorite_feeds_token'):
        checklist.append('share-favorites')

    if not request.user.profile.get_token('userpage_token'):
        checklist.append('userpage')

    if tags_for_user(request.user):
        checklist.append('tags')

    # TODO add podcastlist_count_for_user
    if podcastlists_for_user(request.user.profile.uuid.hex):
        checklist.append('lists')

    if PublishedPodcast.objects.filter(publisher=request.user).exists():
        checklist.append('publish')

    if request.user.profile.get_wksetting(FLATTR_TOKEN):
        checklist.append('flattr')

    if request.user.profile.get_wksetting(FLATTR_AUTO):
        checklist.append('auto-flattr')

    tomorrow = datetime.today() + timedelta(days=1)

    newest_episodes = Episode.objects.filter(podcast__in=subscribed_podcasts,
                                             released__lt=tomorrow).\
                                      select_related('podcast').\
                                      prefetch_related('slugs',
                                                       'podcast__slugs').\
                                      order_by('-released')[:episode_count]


    # we only show the "install reader" link in firefox, because we don't know
    # yet how/if this works in other browsers.
    # hints appreciated at https://bugs.gpodder.org/show_bug.cgi?id=58
    show_install_reader = \
                'firefox' in request.META.get('HTTP_USER_AGENT', '').lower()

    random_podcast = Podcast.objects.all().random().prefetch_related('slugs').first()

    return render(request, 'dashboard.html', {
            'user': request.user,
            'subscribed_podcasts': subscribed_podcasts,
            'newest_episodes': list(newest_episodes),
            'random_podcast': random_podcast,
            'checklist': checklist,
            'site': site,
            'show_install_reader': show_install_reader,
        })


@vary_on_cookie
@cache_control(private=True)
@login_required
def history(request, count=15, uid=None):

    page = parse_range(request.GET.get('page', None), 0, sys.maxint, 0)
    user = request.user

    if uid:
        try:
            device = user.client_set.get(uid=uid)
        except Client.DoesNotExist as e:
            messages.error(request, str(e))

    else:
        device = None

    history_obj = History(request.user, device)

    start = page*count
    end = start+count
    entries = history_obj[start:end]
    HistoryEntry.fetch_data(user, entries)

    return render(request, 'history.html', {
        'history': entries,
        'device': device,
        'page': page,
    })


@never_cache
@login_required
#@slug_id_decorator
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


@vary_on_cookie
@cache_control(private=True)
@login_required
def mytags(request):
    tags_podcast = {}
    tags_tag = defaultdict(list)

    for podcast_id, taglist in tags_for_user(request.user).items():
        podcast = Podcast.objects.get(id=podcast_id)
        tags_podcast[podcast] = taglist

        for tag in taglist:
            tags_tag[ tag ].append(podcast)

    return render(request, 'mytags.html', {
        'tags_podcast': tags_podcast,
        'tags_tag': dict(tags_tag.items()),
    })



class GeventView(View):
    """ View that provides parts of the context via gevent coroutines """

    def get_context(self, context_funs):
        """ returns a dictionary that can be used for a template context

        context_funs is a context-key => Greenlet object mapping """

        if gevent:
            jobs = {}
            for key, fun in context_funs.items():
                jobs[key] = gevent.spawn(fun)

            gevent.joinall(jobs.values())

            for key, gev in jobs.items():
                context_funs[key] = gev.get()

        else:
            for key, fun in context_funs.items():
                context_funs[key] = fun()

        return context_funs
