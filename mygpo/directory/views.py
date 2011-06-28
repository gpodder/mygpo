from itertools import imap as map

from django.core.cache import cache
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.sites.models import RequestSite
from django.views.decorators.cache import cache_page

from mygpo.core.models import Podcast
from mygpo.data.mimetype import CONTENT_TYPES
from mygpo.decorators import manual_gc
from mygpo.directory.models import Category
from mygpo.directory.toplist import PodcastToplist, EpisodeToplist
from mygpo.directory.search import search_podcasts
from mygpo.web import utils
from mygpo.directory.tags import TagCloud
from mygpo.utils import flatten, get_to_dict


@manual_gc
def toplist(request, num=100, lang=None):

    try:
        lang = utils.process_lang_params(request, '/toplist/')
    except utils.UpdatedException, updated:
        return HttpResponseRedirect('/toplist/?lang=%s' % ','.join(updated.data))

    type_str = request.GET.get('types', '')
    set_types = [t for t in type_str.split(',') if t]
    media_types = set_types or CONTENT_TYPES

    toplist = PodcastToplist(lang, media_types)
    entries = toplist[:num]

    max_subscribers = max([p.subscriber_count() for (oldp, p) in entries]) if entries else 0
    current_site = RequestSite(request)
    all_langs = utils.get_language_names(utils.get_podcast_languages())

    return render_to_response('toplist.html', {
        'entries': entries,
        'max_subscribers': max_subscribers,
        'url': current_site,
        'languages': lang,
        'all_languages': all_langs,
        'types': media_types,
    }, context_instance=RequestContext(request))



def browse(request, num_categories=10, num_tags_cloud=90, podcasts_per_category=10):
    num_categories = int(num_categories)
    num_tags_cloud = int(num_tags_cloud)

    # collect Ids of top podcasts in top categories, fetch all at once
    categories = Category.top_categories(num_categories)

    def _prepare_category(category):
        category.entries = category.get_podcasts(0, podcasts_per_category)
        return category

    categories = map(_prepare_category, categories)

    tag_cloud = TagCloud(count=num_tags_cloud, skip=num_categories, sort_by_name=True)

    return render_to_response('directory.html', {
        'categories': categories,
        'tag_cloud': tag_cloud,
        }, context_instance=RequestContext(request))


def category(request, category, page_size=20):
    category = Category.for_tag(category)
    if not category:
        return HttpResponseNotFound()

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    entries = category.get_podcasts( (page-1) * page_size, page*page_size )
    podcasts = filter(None, entries)
    num_pages = len(category.podcasts) / page_size

    page_list = utils.get_page_list(1, num_pages, page, 15)

    return render_to_response('category.html', {
        'entries': podcasts,
        'category': category.label,
        'page_list': page_list,
        }, context_instance=RequestContext(request))



RESULTS_PER_PAGE=20

def search(request):

    if 'q' in request.GET:
        q = request.GET.get('q', '').encode('utf-8')

        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1

        results, total = search_podcasts(q=q, skip=RESULTS_PER_PAGE*(page-1))
        num_pages = total / RESULTS_PER_PAGE

        page_list = utils.get_page_list(1, num_pages, page, 15)

    else:
        results = None
        q = None
        page_list = []

    return render_to_response('search.html', {
            'q': q,
            'results': results,
            'page_list': page_list,
        }, context_instance=RequestContext(request))



@manual_gc
def episode_toplist(request, num=100):

    try:
        lang = utils.process_lang_params(request, '/toplist/episodes')
    except utils.UpdatedException, updated:
        return HttpResponseRedirect('/toplist/episodes?lang=%s' % ','.join(updated.data))

    type_str = request.GET.get('types', '')
    set_types = filter(None, type_str.split(','))

    media_types = set_types or CONTENT_TYPES

    toplist = EpisodeToplist(languages=lang, types=media_types)
    entries = toplist[:num]

    current_site = RequestSite(request)

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
        'all_types': CONTENT_TYPES,
    }, context_instance=RequestContext(request))
