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
from django.http import HttpResponseRedirect
from django.template import RequestContext
from mygpo.api import backend
from mygpo.data.mimetype import CONTENT_TYPES
from mygpo.decorators import manual_gc
from mygpo.web import utils
from django.contrib.sites.models import Site



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


