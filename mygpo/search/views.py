from django.shortcuts import render_to_response
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext
from mygpo.search.models import SearchEntry
from mygpo.search.util import simple_search

def search(request):

    page_size = 20

    if 'q' in request.GET:
        q = request.GET.get('q', '').encode('utf-8')
        entries = simple_search(q)
        paginator = Paginator(entries, page_size)

        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1

        try:
            results = paginator.page(page)
        except (EmptyPage, InvalidPage):
            results = paginator.page(paginator.num_pages)

    else:
        results = None
        q = None

    return render_to_response('search.html', {
            'q': q,
            'results': results,
        }, context_instance=RequestContext(request))

