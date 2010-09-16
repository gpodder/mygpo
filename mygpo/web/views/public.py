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

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, Http404, HttpResponseForbidden
from django.template import RequestContext
from mygpo.api.models import Podcast, Episode, Subscription
from mygpo.api import backend
from mygpo.data.models import PodcastTag, DirectoryEntry
from mygpo.data.mimetype import CONTENT_TYPES
from mygpo.decorators import manual_gc
from mygpo.web import utils
from mygpo import settings
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.contrib.sites.models import Site
from django.core.paginator import Paginator, InvalidPage, EmptyPage


@manual_gc
def browse(request, num_categories=10, num_tags_cloud=90, podcasts_per_category=10):
    total = int(num_categories) + int(num_tags_cloud)
    top_tags =  DirectoryEntry.objects.top_tags(total)

    categories = []
    for tag in top_tags[:num_categories]:
        entries = DirectoryEntry.objects.podcasts_for_tag(tag.tag)[:podcasts_per_category]
        categories.append({
            'tag': tag.tag,
            'entries': entries
            })

    tag_cloud = top_tags[num_categories:]

    tag_cloud.sort(key = lambda x: x.tag.lower())
    max_entries = max([t.entries for t in tag_cloud])

    return render_to_response('directory.html', {
        'categories': categories,
        'tag_cloud': tag_cloud,
        'max_entries': max_entries,
        }, context_instance=RequestContext(request))


@manual_gc
def category(request, category, page_size=20):
    entries = DirectoryEntry.objects.podcasts_for_tag(category)

    paginator = Paginator(entries, page_size)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        podcasts = paginator.page(page)
    except (EmptyPage, InvalidPage):
        podcasts = paginator.page(paginator.num_pages)

    page_list = utils.get_page_list(1, podcasts.paginator.num_pages, podcasts.number, 15)

    return render_to_response('category.html', {
        'entries': podcasts,
        'category': category,
        'page_list': page_list,
        }, context_instance=RequestContext(request))


@manual_gc
def toplist(request, num=100, lang=None):

    try:
        lang = utils.process_lang_params(request, '/toplist/')
    except utils.UpdatedException, updated:
        return HttpResponseRedirect('/toplist/?lang=%s' % ','.join(updated.data))

    type_str = request.GET.get('types', '')
    set_types = [t for t in type_str.split(',') if t]
    if set_types:
        media_types = dict([(t, t in set_types) for t in CONTENT_TYPES])
    else:
        media_types = dict([(t, True) for t in CONTENT_TYPES])

    entries = backend.get_toplist(num, lang, set_types)

    max_subscribers = max([e.subscriptions for e in entries]) if entries else 0
    current_site = Site.objects.get_current()
    all_langs = utils.get_language_names(utils.get_podcast_languages())

    return render_to_response('toplist.html', {
        'entries': entries,
        'max_subscribers': max_subscribers,
        'url': current_site,
        'languages': lang,
        'all_languages': all_langs,
        'types': media_types,
    }, context_instance=RequestContext(request))


@manual_gc
def episode_toplist(request, num=100):

    try:
        lang = utils.process_lang_params(request, '/toplist/episodes')
    except utils.UpdatedException, updated:
        return HttpResponseRedirect('/toplist/episodes?lang=%s' % ','.join(updated.data))

    type_str = request.GET.get('types', '')
    set_types = [t for t in type_str.split(',') if t]
    if set_types:
        media_types = dict([(t, t in set_types) for t in CONTENT_TYPES])
    else:
        media_types = dict([(t, True) for t in CONTENT_TYPES])

    entries = backend.get_episode_toplist(num, lang, set_types)

    current_site = Site.objects.get_current()

    # Determine maximum listener amount (or 0 if no entries exist)
    max_listeners = max([0]+[e.listeners for e in entries])
    all_langs = utils.get_language_names(utils.get_podcast_languages())
    return render_to_response('episode_toplist.html', {
        'entries': entries,
        'max_listeners': max_listeners,
        'url': current_site,
        'languages': lang,
        'all_languages': all_langs,
        'types': media_types,
    }, context_instance=RequestContext(request))


def gpodder_example_podcasts(request):
    sponsored_podcast = utils.get_sponsored_podcast()
    return render_to_response('gpodder_examples.opml', {
       'sponsored_podcast': sponsored_podcast
    }, context_instance=RequestContext(request))


