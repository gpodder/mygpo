from __future__ import division

from itertools import imap as map
from math import ceil

from django.http import HttpResponseNotFound, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.contrib.sites.models import RequestSite
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_cookie
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _

from feedservice.parse.models import ParserException
from feedservice.parse import FetchFeedException

from mygpo.core.proxy import proxy_object
from mygpo.directory.toplist import PodcastToplist, EpisodeToplist, \
         TrendingPodcasts
from mygpo.directory.search import search_podcasts
from mygpo.web.utils import process_lang_params, get_language_names, \
         get_page_list, get_podcast_link_target
from mygpo.directory.tags import Topics
from mygpo.users.models import User
from mygpo.users.settings import FLATTR_TOKEN
from mygpo.data.feeddownloader import PodcastUpdater, NoEpisodesException
from mygpo.db.couchdb.podcast import get_podcast_languages, podcasts_by_id, \
         random_podcasts, podcasts_to_dict, podcast_for_url, \
         get_flattr_podcasts, get_flattr_podcast_count
from mygpo.db.couchdb.directory import category_for_tag
from mygpo.db.couchdb.podcastlist import random_podcastlists, \
         podcastlist_count, podcastlists_by_rating


@vary_on_cookie
@cache_control(private=True)
def toplist(request, num=100, lang=None):

    lang = process_lang_params(request)

    toplist = PodcastToplist(lang)
    entries = toplist[:num]

    max_subscribers = max([p.subscriber_count() for (oldp, p) in entries]) if entries else 0
    current_site = RequestSite(request)

    languages = get_podcast_languages()
    all_langs = get_language_names(languages)

    return render(request, 'toplist.html', {
        'entries': entries,
        'max_subscribers': max_subscribers,
        'url': current_site,
        'language': lang,
        'all_languages': all_langs,
    })


class Carousel(View):
    """ A carousel demo """

    @method_decorator(cache_control(private=True))
    @method_decorator(vary_on_cookie)
    def get(self, request):

        return render(request, 'carousel.html', {
            # evaluated lazyly, cached by template
            'topics': Topics(),
            })


class Directory(View):
    """ The main directory page """

    @method_decorator(cache_control(private=True))
    @method_decorator(vary_on_cookie)
    def get(self, request):

        return render(request, 'directory.html', {

            # evaluated lazyly, cached by template
            'topics': Topics(),
            'trending_podcasts': TrendingPodcasts(''),
            'podcastlists': self.get_random_list(),
            'random_podcasts': self.get_random_podcast(),
            })


    def get_random_list(self, podcasts_per_list=5):
        random_list = next(random_podcastlists(), None)
        list_owner = None
        if random_list:
            random_list = proxy_object(random_list)
            random_list.more_podcasts = max(0, len(random_list.podcasts) - podcasts_per_list)
            random_list.podcasts = podcasts_by_id(random_list.podcasts[:podcasts_per_list])
            random_list.user = User.get(random_list.user)

        yield random_list

    def get_random_podcast(self):
        random_podcast = next(random_podcasts(), None)
        if random_podcast:
            yield random_podcast.get_podcast()


@cache_control(private=True)
@vary_on_cookie
def category(request, category, page_size=20):
    category = category_for_tag(category)
    if not category:
        return HttpResponseNotFound()

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    entries = category.get_podcasts( (page-1) * page_size, page*page_size )
    podcasts = filter(None, entries)
    num_pages = int(ceil(len(category.podcasts) / page_size))

    page_list = get_page_list(1, num_pages, page, 15)

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
        num_pages = int(ceil(total / RESULTS_PER_PAGE))

        page_list = get_page_list(1, num_pages, page, 15)

    else:
        results = []
        q = None
        page_list = []

    max_subscribers = max([p.subscriber_count() for p in results] + [0])
    current_site = RequestSite(request)

    return render(request, template, dict(
            q= q,
            results= results,
            page_list= page_list,
            max_subscribers= max_subscribers,
            domain= current_site.domain,
            **args
            ))


@cache_control(private=True)
@vary_on_cookie
def episode_toplist(request, num=100):
    lang = process_lang_params(request)

    toplist = EpisodeToplist(language=lang)
    entries = list(map(proxy_object, toplist[:num]))

    # load podcast objects
    podcast_ids = [e.podcast for e in entries]
    podcasts = podcasts_to_dict(podcast_ids, True)
    for entry in entries:
        entry.podcast = podcasts.get(entry.podcast, None)

    current_site = RequestSite(request)

    # Determine maximum listener amount (or 0 if no entries exist)
    max_listeners = max([0]+[e.listeners for e in entries])

    languages = get_podcast_languages()
    all_langs = get_language_names(languages)

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

    lists = podcastlists_by_rating(skip=(page-1) * page_size, limit=page_size)


    def _prepare_list(l):
        user = User.get(l.user)
        l = proxy_object(l)
        l.username = user.username
        return l

    lists = map(_prepare_list, lists)

    num_pages = int(ceil(podcastlist_count() / float(page_size)))

    page_list = get_page_list(1, num_pages, page, 15)

    return render(request, 'podcast_lists.html', {
        'lists': lists,
        'page_list': page_list,
        })



class MissingPodcast(View):
    """ Check if a podcast is missing """

    @method_decorator(login_required)
    def get(self, request):

        site = RequestSite(request)

        # check if we're doing a query
        url = request.GET.get('q', None)

        if not url:
            podcast = None
            can_add = False

        else:
            podcast = podcast_for_url(url)

            # if the podcast does already exist, there's nothing more to do
            if podcast:
                can_add = False

            # check if we could add a podcast for the given URL
            else:
                podcast = False
                updater = PodcastUpdater()

                try:
                    can_add = updater.verify_podcast_url(url)

                except (ParserException, FetchFeedException,
                        NoEpisodesException) as ex:
                    can_add = False
                    messages.error(request, str(ex))

        return render(request, 'missing.html', {
                'site': site,
                'q': url,
                'podcast': podcast,
                'can_add': can_add,
            })


class AddPodcast(View):
    """ Add a missing podcast"""

    @method_decorator(login_required)
    @method_decorator(cache_control(private=True))
    @method_decorator(vary_on_cookie)
    def post(self, request):

        url = request.POST.get('url', None)

        if not url:
            raise Http404

        updater = PodcastUpdater()

        try:
            podcast = updater.update(url)

            messages.success(request, _('The podcast has been added'))

            return HttpResponseRedirect(get_podcast_link_target(podcast))

        except (ParserException, FetchFeedException,
                NoEpisodesException) as ex:
            messages.error(request, str(ex))

            add_page = '%s?q=%s' % (reverse('missing-podcast'), url)
            return HttpResponseRedirect(add_page)



class FlattrPodcastList(View):
    """ Lists podcasts that have Flattr payment URLs """

    @method_decorator(cache_control(private=True))
    @method_decorator(vary_on_cookie)
    def get(self, request, page_size=20):

        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        podcasts = get_flattr_podcasts( (page-1) * page_size, page_size)
        podcast_count = get_flattr_podcast_count()
        num_pages = int(ceil(podcast_count / page_size))
        page_list = get_page_list(1, num_pages, page, 15)

        max_subscribers = max([p.subscriber_count() for p in podcasts] + [0])

        user = request.user
        flattr_auth = user.is_authenticated() and bool(user.get_wksetting(FLATTR_TOKEN))

        return render(request, 'flattr-podcasts.html', {
            'podcasts': podcasts,
            'page_list': page_list,
            'current_page': page,
            'flattr_auth': flattr_auth,
            'max_subscribers': max_subscribers,
            })
