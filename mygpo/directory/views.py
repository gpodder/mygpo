from itertools import imap as map, islice
from math import ceil

from django.core.cache import cache
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
from django.contrib.sites.models import RequestSite
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_cookie

from mygpo.core.models import Podcast
from mygpo.core.proxy import proxy_object
from mygpo.data.mimetype import CONTENT_TYPES
from mygpo.directory.models import Category
from mygpo.directory.topics import Topics
from mygpo.directory.toplist import PodcastToplist, EpisodeToplist
from mygpo.directory.search import search_podcasts
from mygpo.web import utils
from mygpo.directory.tags import TagCloud
from mygpo.utils import flatten, get_to_dict
from mygpo.share.models import PodcastList
from mygpo.users.models import User
from mygpo.cache import get_cache_or_calc


@vary_on_cookie
@cache_control(private=True)
def toplist(request, num=100, lang=None):

    lang = utils.process_lang_params(request)

    toplist = PodcastToplist(lang)
    entries = toplist[:num]

    max_subscribers = max([p.subscriber_count() for (oldp, p) in entries]) if entries else 0
    current_site = RequestSite(request)

    languages = get_cache_or_calc('podcast-languages', timeout=60*60,
            calc=lambda: utils.get_podcast_languages())
    all_langs = utils.get_language_names(languages)

    return render(request, 'toplist.html', {
        'entries': entries,
        'max_subscribers': max_subscribers,
        'url': current_site,
        'language': lang,
        'all_languages': all_langs,
    })



@cache_control(private=True)
@vary_on_cookie
def browse(request, num_lists=4, num_categories=10, num_tags_cloud=90,
        podcasts_per_topic=10):

    num_lists      = int(num_lists)
    num_categories = int(num_categories)
    num_tags_cloud = int(num_tags_cloud)

    topics = Topics(num_lists, num_categories, podcasts_per_topic)
    topics = islice(topics, 0, num_categories)

    tag_cloud = TagCloud(count=num_tags_cloud, skip=num_categories, sort_by_name=True)

    return render(request, 'directory.html', {
        'topics': topics,
        'tag_cloud': tag_cloud,
        })


@cache_control(private=True)
@vary_on_cookie
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

    return render(request, 'category.html', {
        'entries': podcasts,
        'category': category.label,
        'page_list': page_list,
        })



RESULTS_PER_PAGE=20

@cache_control(private=True)
@vary_on_cookie
def search(request, template='search.html', args={}):

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
        results = []
        q = None
        page_list = []

    max_subscribers = max([p.subscriber_count() for p in results] + [0])

    return render(request, template, dict(
            q= q,
            results= results,
            page_list= page_list,
            max_subscribers= max_subscribers,
            **args
            ))


@cache_control(private=True)
@vary_on_cookie
def episode_toplist(request, num=100):

    lang = utils.process_lang_params(request)

    toplist = EpisodeToplist(language=lang)
    entries = list(map(proxy_object, toplist[:num]))

    # load podcast objects
    podcast_ids = [e.podcast for e in entries]
    podcasts = get_to_dict(Podcast, podcast_ids, Podcast.get_id, True)
    for entry in entries:
        entry.podcast = podcasts.get(entry.podcast, None)

    current_site = RequestSite(request)

    # Determine maximum listener amount (or 0 if no entries exist)
    max_listeners = max([0]+[e.listeners for e in entries])

    languages = get_cache_or_calc('podcast-languages', timeout=60*60,
            calc=lambda: utils.get_podcast_languages())
    all_langs = utils.get_language_names(languages)

    return render(request, 'episode_toplist.html', {
        'entries': entries,
        'max_listeners': max_listeners,
        'url': current_site,
        'language': lang,
        'all_languages': all_langs,
    })


@cache_control(private=True)
@vary_on_cookie
def podcast_lists(request, page_size=20):

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    lists = PodcastList.by_rating(skip=(page-1) * page_size, limit=page_size)


    def _prepare_list(l):
        user = User.get(l.user)
        l = proxy_object(l)
        l.username = user.username
        return l

    lists = map(_prepare_list, lists)

    num_pages = int(ceil(PodcastList.count() / float(page_size)))

    page_list = utils.get_page_list(1, num_pages, page, 15)

    return render(request, 'podcast_lists.html', {
        'lists': lists,
        'page_list': page_list,
        })
