from django.http import HttpResponseNotFound
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import render_to_response
from django.template import RequestContext

from mygpo.directory.models import Category
from mygpo.web import utils


def browse(request, num_categories=10, num_tags_cloud=90, podcasts_per_category=10):
    total = int(num_categories) + int(num_tags_cloud)
    categories = Category.top_categories(total).all()

    disp_categories = []
    for category in categories[:num_categories]:
        entries = category.get_podcasts(0, podcasts_per_category)
        podcasts = [e.get_old_obj() for e in entries]
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
    podcasts = [e.get_old_obj() for e in entries]
    num_pages = len(category.podcasts) / page_size

    page_list = utils.get_page_list(1, num_pages, page, 15)

    return render_to_response('category.html', {
        'entries': podcasts,
        'category': category.label,
        'page_list': page_list,
        }, context_instance=RequestContext(request))


