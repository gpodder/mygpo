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
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.decorators.cache import cache_page
from django.contrib.auth.models import User
from django.template import RequestContext
from mygpo.core import models
from mygpo.directory import tags
from mygpo.directory.toplist import PodcastToplist
from mygpo.users.models import Rating, Suggestions, History, HistoryEntry
from mygpo.api.models import Podcast, Episode, Device, EpisodeAction, UserProfile
from mygpo.users.models import PodcastUserState
from mygpo.decorators import manual_gc
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from datetime import datetime, timedelta
from django.contrib.sites.models import RequestSite
from mygpo.web import utils
from mygpo.api import backend
from mygpo.utils import flatten, parse_range
from mygpo import migrate
import os
import Image
import ImageDraw
import StringIO


def home(request):
    if request.user.is_authenticated():
        return dashboard(request)
    else:
        return welcome(request)


@manual_gc
def welcome(request, toplist_entries=10):
    current_site = RequestSite(request)
    podcasts = Podcast.objects.count()
    users = User.objects.filter(is_active=True).count()
    episodes = models.Episode.count()

    try:
        lang = utils.process_lang_params(request, '/toplist/')
    except utils.UpdatedException, updated:
        lang = []

    toplist = PodcastToplist(lang)
    entries = toplist[:toplist_entries]

    toplist = [p for (oldpos, p) in entries]

    return render_to_response('home.html', {
          'podcast_count': podcasts,
          'user_count': users,
          'episode_count': episodes,
          'url': current_site,
          'toplist': toplist,
    }, context_instance=RequestContext(request))


@manual_gc
@login_required
def dashboard(request, episode_count=10):
    site = RequestSite(request)
    devices = Device.objects.filter(user=request.user, deleted=False)

    user = migrate.get_or_migrate_user(request.user)
    subscribed_podcasts = user.get_subscribed_podcasts()
    subscribed_old_podcasts = [x.get_old_obj() for x in subscribed_podcasts]

    tomorrow = datetime.today() + timedelta(days=1)
    newest_episodes = user.get_newest_episodes(tomorrow)
    newest_episodes = islice(newest_episodes, 0, episode_count)

    lang = utils.get_accepted_lang(request)
    lang = utils.sanitize_language_codes(lang)

    random_podcasts = backend.get_random_picks(lang)[:5]
    random_podcasts = map(migrate.get_or_migrate_podcast, random_podcasts)

    return render_to_response('dashboard.html', {
            'site': site,
            'devices': devices,
            'subscribed_podcasts': subscribed_podcasts,
            'newest_episodes': newest_episodes,
            'random_podcasts': random_podcasts,
        }, context_instance=RequestContext(request))


@cache_page(60 * 60 * 24)
def cover_art(request, size, filename):
    size = int(size)

    # XXX: Is there a "cleaner" way to get the root directory of the installation?
    root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
    target = os.path.join(root, 'htdocs', 'media', 'logo', str(size), filename+'.jpg')
    filepath = os.path.join(root, 'htdocs', 'media', 'logo', filename)

    if os.path.exists(target):
        return HttpResponseRedirect('/media/logo/%s/%s.jpg' % (str(size), filename))

    if os.path.exists(filepath):
        target_dir = os.path.dirname(target)
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)

        try:
            im = Image.open(filepath)
            if im.mode not in ('RGB', 'RGBA'):
                im = im.convert('RGB')
        except:
            raise Http404('Cannot open cover file')

        try:
            resized = im.resize((size, size), Image.ANTIALIAS)
        except IOError:
            # raised when trying to read an interlaced PNG; we use the original instead
            return HttpResponseRedirect('/media/logo/%s' % filename)

        # If it's a RGBA image, composite it onto a white background for JPEG
        if resized.mode == 'RGBA':
            background = Image.new('RGB', resized.size)
            draw = ImageDraw.Draw(background)
            draw.rectangle((-1, -1, resized.size[0]+1, resized.size[1]+1), \
                    fill=(255, 255, 255))
            del draw
            resized = Image.composite(resized, background, resized)

        io = StringIO.StringIO()
        resized.save(io, 'JPEG', optimize=True, progression=True, quality=80)
        s = io.getvalue()

        fp = open(target, 'wb')
        fp.write(s)
        fp.close()

        return HttpResponseRedirect('/media/logo/%s/%s.jpg' % (str(size), filename))
    else:
        raise Http404('Cover art not available')

@manual_gc
@login_required
def history(request, count=15, device_id=None):

    page = parse_range(request.GET.get('page', None), 0, sys.maxint, 0)

    user = migrate.get_or_migrate_user(request.user)

    if device_id:
        device = get_object_or_404(Device, id=device_id, user=request.user)
        device = migrate.get_or_migrate_device(device)
    else:
        device = None

    history_obj = History(user, device)

    start = page*count
    end = start+count
    entries = list(history_obj[start:end])
    HistoryEntry.fetch_data(user, entries)

    return render_to_response('history.html', {
        'history': entries,
        'device': device,
        'page': page,
    }, context_instance=RequestContext(request))


@login_required
def blacklist(request, podcast_id):
    blacklisted_podcast = models.Podcast.for_oldid(podcast_id)
    suggestion = Suggestions.for_user_oldid(request.user.id)
    suggestion.blacklist.append(blacklisted_podcast._id)
    suggestion.save()

    p, _created = UserProfile.objects.get_or_create(user=request.user)
    p.suggestion_up_to_date = False
    p.save()

    return HttpResponseRedirect(reverse('suggestions'))


@login_required
def rate_suggestions(request):
    rating_val = int(request.GET.get('rate', None))

    if rating_val in (1, -1):
        suggestion = Suggestions.for_user_oldid(request.user.id)
        rating = Rating(rating=rating_val)
        suggestion.ratings.append(rating)
        suggestion.save()
        # TODO: when we use Django messaging system,
        # add a message for successful rating here


    return HttpResponseRedirect(reverse('suggestions'))


@login_required
def suggestions(request):
    suggestion_obj = Suggestions.for_user_oldid(request.user.id)
    suggestions = suggestion_obj.get_podcasts()
    current_site = RequestSite(request)
    return render_to_response('suggestions.html', {
        'entries': suggestions,
        'url': current_site
    }, context_instance=RequestContext(request))


@login_required
def mytags(request):
    tags_podcast = {}
    tags_tag = defaultdict(list)

    for podcast_id, taglist in tags.tags_for_user(request.user).items():
        podcast = models.Podcast.get(podcast_id)
        tags_podcast[podcast] = taglist

        for tag in taglist:
            tags_tag[ tag ].append(podcast)

    return render_to_response('mytags.html', {
        'tags_podcast': tags_podcast,
        'tags_tag': dict(tags_tag.items()),
    }, context_instance=RequestContext(request))
