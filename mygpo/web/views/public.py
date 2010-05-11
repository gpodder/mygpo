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
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, Http404, HttpResponseForbidden
from django.template import RequestContext
from mygpo.api.models import Podcast, Episode, ToplistEntry, Subscription
from mygpo.data.models import PodcastTag
from mygpo.decorators import manual_gc
from mygpo import settings
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.contrib.sites.models import Site
from django.core.paginator import Paginator, InvalidPage, EmptyPage


@manual_gc
def browse(request, num_categories=10, num_tags_cloud=90, podcasts_per_category=10):
    total = int(num_categories) + int(num_tags_cloud)
    top_tags =  PodcastTag.objects.raw("select *, count(id) as entries from podcast_tags group by tag order by entries desc limit %d" % total)

    top_tags = filter(lambda x: not x.tag.startswith('http://'), top_tags)

    excluded_tags = getattr(settings, 'DIRECTORY_EXCLUDED_TAGS', [])
    top_tags = filter(lambda x: not x.tag in excluded_tags, top_tags)

    categories = []
    for tag in top_tags[:num_categories]:
        entries = ToplistEntry.objects.filter(podcast__podcasttag__tag=tag.tag).order_by('-subscriptions').distinct()[:podcasts_per_category]
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
    entries = ToplistEntry.objects.filter(podcast__podcasttag__tag=category).order_by('-subscriptions')

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

    return render_to_response('category.html', {
        'entries': podcasts,
        'category': category,
        }, context_instance=RequestContext(request))


