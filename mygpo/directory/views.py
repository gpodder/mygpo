from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.sites.models import RequestSite
from django.views.decorators.cache import cache_page

from mygpo.api import backend
from mygpo.data.mimetype import CONTENT_TYPES
from mygpo.decorators import manual_gc, cache_page_anonymous
from mygpo.directory.models import Category
from mygpo.directory.search import search_podcasts
from mygpo.web import utils


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



@cache_page_anonymous(60 * 60 * 24)
def browse(request, num_categories=10, num_tags_cloud=90, podcasts_per_category=10):
    total = int(num_categories) + int(num_tags_cloud)
    categories = Category.top_categories(total).all()

    disp_categories = []
    for category in categories[:num_categories]:
        entries = category.get_podcasts(0, podcasts_per_category)
        podcasts = filter(None, entries)
        disp_categories.append({
            'tag': category.label,
            'entries': podcasts,
            })

    tag_cloud = categories[num_categories:]

    tag_cloud.sort(key = lambda x: x.label.lower())
    max_entries = max([t.get_weight() for t in tag_cloud] + [0])

    return render_to_response('directory.html', {
        'categories': disp_categories,
        'tag_cloud': tag_cloud,
        'max_entries': max_entries,
        }, context_instance=RequestContext(request))


@cache_page_anonymous(60 * 60 * 24)
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
