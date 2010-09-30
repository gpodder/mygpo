from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import render_to_response
from django.template import RequestContext

from mygpo.data.models import DirectoryEntry
from mygpo.directory.models import Category
from mygpo.web import utils

def browse(request, num_categories=10, num_tags_cloud=90, podcasts_per_category=10):
    total = int(num_categories) + int(num_tags_cloud)
    categories = Category.top_categories(total).all()

    disp_categories = []
    for category in categories[:num_categories]:
        entries = DirectoryEntry.objects.podcasts_for_category(category.get_tags())[:podcasts_per_category]
        disp_categories.append({
            'tag': category.label,
            'entries': entries
            })

    tag_cloud = categories[num_categories:]

    tag_cloud.sort(key = lambda x: x.label.lower())
    max_entries = max([t.weight for t in tag_cloud])

    return render_to_response('directory.html', {
        'categories': disp_categories,
        'tag_cloud': tag_cloud,
        'max_entries': max_entries,
        }, context_instance=RequestContext(request))


def category(request, category, page_size=20):
    category = Category.for_tag(category)
    entries = DirectoryEntry.objects.podcasts_for_category(category.get_tags())

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
        'category': category.label,
        'page_list': page_list,
        }, context_instance=RequestContext(request))


