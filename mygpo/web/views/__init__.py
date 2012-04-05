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
from itertools import islice
from collections import defaultdict
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.sites.models import RequestSite
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control

from mygpo.decorators import repeat_on_conflict
from mygpo.core import models
from mygpo.core.models import Podcast, Episode
from mygpo.directory.tags import Tag
from mygpo.directory.toplist import PodcastToplist
from mygpo.users.models import Suggestions, History, HistoryEntry
from mygpo.users.models import PodcastUserState, User
from mygpo.web import utils
from mygpo.api import backend
from mygpo.utils import flatten, parse_range
from mygpo.cache import get_cache_or_calc


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

    podcasts = get_cache_or_calc('podcast-count', timeout=60*60,
                    calc=lambda: Podcast.count())
    users    = get_cache_or_calc('user-count', timeout=60*60,
                    calc=lambda: User.count())
    episodes = get_cache_or_calc('episode-count', timeout=60*60,
                    calc=lambda: Episode.count())

    lang = utils.process_lang_params(request)

    toplist = PodcastToplist(lang)

    return render(request, 'home.html', {
          'podcast_count': podcasts,
          'user_count': users,
          'episode_count': episodes,
          'url': current_site,
          'toplist': toplist,
    })


@vary_on_cookie
@cache_control(private=True)
@login_required
def dashboard(request, episode_count=10):

    site = RequestSite(request)

    user = request.user
    subscribed_podcasts = user.get_subscribed_podcasts()
    devices = user.active_devices

    tomorrow = datetime.today() + timedelta(days=1)
    newest_episodes = user.get_newest_episodes(tomorrow)
    newest_episodes = islice(newest_episodes, 0, episode_count)

    lang = utils.get_accepted_lang(request)
    lang = utils.sanitize_language_codes(lang)

    random_podcasts = islice(backend.get_random_picks(lang), 0, 5)

    return render(request, 'dashboard.html', {
            'site': site,
            'devices': devices,
            'subscribed_podcasts': subscribed_podcasts,
            'newest_episodes': newest_episodes,
            'random_podcasts': random_podcasts,
        })


@vary_on_cookie
@cache_control(private=True)
@login_required
def history(request, count=15, uid=None):

    page = parse_range(request.GET.get('page', None), 0, sys.maxint, 0)

    if uid:
        device = request.user.get_device_by_uid(uid)
    else:
        device = None

    history_obj = History(request.user, device)

    start = page*count
    end = start+count
    entries = list(history_obj[start:end])
    HistoryEntry.fetch_data(request.user, entries)

    return render(request, 'history.html', {
        'history': entries,
        'device': device,
        'page': page,
    })


@never_cache
@login_required
def blacklist(request, podcast_id):
    podcast_id = int(podcast_id)
    blacklisted_podcast = Podcast.for_oldid(podcast_id)

    suggestion = Suggestions.for_user(request.user)

    @repeat_on_conflict(['suggestion'])
    def _update(suggestion, podcast_id):
        suggestion.blacklist.append(podcast_id)
        suggestion.save()

    _update(suggestion=suggestion, podcast_id=blacklisted_podcast.get_id())

    request.user.suggestions_up_to_date = False
    request.user.save()

    return HttpResponseRedirect(reverse('suggestions'))


@never_cache
@login_required
def rate_suggestions(request):
    rating_val = int(request.GET.get('rate', None))

    suggestion = Suggestions.for_user(request.user)
    suggestion.rate(rating_val, request.user._id)
    suggestion.save()

    messages.success(request, _('Thanks for rating!'))

    return HttpResponseRedirect(reverse('suggestions'))


@vary_on_cookie
@cache_control(private=True)
@login_required
def suggestions(request):
    suggestion_obj = Suggestions.for_user(request.user)
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

    for podcast_id, taglist in Tag.for_user(request.user).items():
        podcast = Podcast.get(podcast_id)
        tags_podcast[podcast] = taglist

        for tag in taglist:
            tags_tag[ tag ].append(podcast)

    return render(request, 'mytags.html', {
        'tags_podcast': tags_podcast,
        'tags_tag': dict(tags_tag.items()),
    })
