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
from django.views.generic.base import View, TemplateView
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
from mygpo.users.settings import FLATTR_TOKEN
from mygpo.data.feeddownloader import PodcastUpdater, NoEpisodesException
from mygpo.data.tasks import update_podcasts
from mygpo.db.couchdb.user import get_user_by_id
from mygpo.db.couchdb.podcast import get_podcast_languages, podcasts_by_id, \
         random_podcasts, podcasts_to_dict, podcast_for_url, \
         get_flattr_podcasts, get_flattr_podcast_count, get_license_podcasts, \
         get_license_podcast_count
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
            random_list.user = get_user_by_id(random_list.user)

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
        user = get_user_by_id(l.user)
        l = proxy_object(l)
        l.username = user.username if user else ''
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
                    messages.error(request, unicode(ex))

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

        res = update_podcasts.delay([url])

        return HttpResponseRedirect(reverse('add-podcast-status',
                args=[res.task_id]))


class AddPodcastStatus(TemplateView):
    """ Status of adding a podcast """

    template_name = 'directory/add-podcast-status.html'

    def get(self, request, task_id):
        result = update_podcasts.AsyncResult(task_id)

        if not result.ready():
            return self.render_to_response({
                'ready': False,
            })

        try:
            podcasts = result.get()
            messages.success(request, _('%d podcasts added' % len(podcasts)))

        except (ParserException, FetchFeedException,
                NoEpisodesException) as ex:
            messages.error(request, str(ex))
            podcast = None

        return self.render_to_response({
                'ready': True,
                'podcasts': podcasts,
            })


class PodcastListView(TemplateView):
    """ A generic podcast list view """

    @method_decorator(cache_control(private=True))
    @method_decorator(vary_on_cookie)
    def get(self, request, page_size=20):

        page = self.get_page(request)
        podcasts = self.get_podcasts( (page-1) * page_size, page_size)
        podcast_count = self.get_podcast_count()

        context = {
            'podcasts': podcasts,
            'page_list': self.get_page_list(page, page_size, podcast_count),
            'current_page': page,
            'max_subscribers': self.get_max_subscribers(podcasts),
        }

        context.update(self.other_context(request))

        return self.render_to_response(context)


    def get_podcasts(self, offset, limit):
        """ must return a list of podcasts """
        raise NotImplemented

    def get_podcast_count():
        """ must return the total number of podcasts """
        raise NotImplemented

    def other_context(self, request):
        """ can return a dict of additional context data """
        return {}

    def get_page(self, request):
        # Make sure page request is an int. If not, deliver first page.
        try:
            return int(request.GET.get('page', '1'))
        except ValueError:
            return 1

    def get_page_list(self, page, page_size, podcast_count):
        num_pages = int(ceil(podcast_count / page_size))
        return get_page_list(1, num_pages, page, 15)

    def get_max_subscribers(self, podcasts):
        return max([p.subscriber_count() for p in podcasts] + [0])


class FlattrPodcastList(PodcastListView):
    """ Lists podcasts that have Flattr payment URLs """

    template_name = 'flattr-podcasts.html'
    get_podcasts = staticmethod(get_flattr_podcasts)
    get_podcast_count = staticmethod(get_flattr_podcast_count)

    def other_context(self, request):
        user = request.user
        return {
            'flattr_auth': user.is_authenticated() and
                           bool(user.get_wksetting(FLATTR_TOKEN))
        }


class LicensePodcastList(PodcastListView):
    """ Lists podcasts that have license information """

    template_name = 'directory/license-podcasts.html'
    get_podcasts = staticmethod(get_license_podcasts)
    get_podcast_count = staticmethod(get_license_podcast_count)
