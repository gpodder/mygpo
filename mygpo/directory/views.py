


from math import ceil
from collections import Counter

from django.http import HttpResponseNotFound, Http404, HttpResponseRedirect
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.db.models import Count
from django.contrib.sites.requests import RequestSite
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast, Episode
from mygpo.directory.search import search_podcasts
from mygpo.web.utils import process_lang_params, get_language_names, \
         get_page_list, get_podcast_link_target, sanitize_language_codes
from mygpo.directory.tags import Topics
from mygpo.users.settings import FLATTR_TOKEN
from mygpo.categories.models import Category
from mygpo.podcastlists.models import PodcastList
from mygpo.data.feeddownloader import (verify_podcast_url, NoEpisodesException,
    UpdatePodcastException)
from mygpo.data.tasks import update_podcasts


class ToplistView(TemplateView):
    """ Generic Top List view """

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_control(private=True))
    def dispatch(self, *args, **kwargs):
        """ Only used for applying decorators """
        return super(ToplistView, self).dispatch(*args, **kwargs)

    def all_languages(self):
        """ Returns all 2-letter language codes that are used by podcasts.

        It filters obviously invalid strings, but does not check if any
        of these codes is contained in ISO 639. """

        query = Podcast.objects.exclude(language__isnull=True)
        query = query.distinct('language').values('language')

        langs = [o['language'] for o in query]
        langs = sorted(sanitize_language_codes(langs))

        return get_language_names(langs)

    def language(self):
        """ Currently selected language """
        return process_lang_params(self.request)

    def site(self):
        """ Current site for constructing absolute links """
        return RequestSite(self.request)


class PodcastToplistView(ToplistView):
    """ Most subscribed podcasts """

    template_name = 'toplist.html'

    def get_context_data(self, num=100):
        context = super(PodcastToplistView, self).get_context_data()

        entries = Podcast.objects.all()\
                                 .prefetch_related('slugs')\
                                 .toplist(self.language())[:num]
        context['entries'] = entries

        context['max_subscribers'] = max([0] + [p.subscriber_count() for p in entries])

        return context


class EpisodeToplistView(ToplistView):
    """ Most listened-to episodes """

    template_name = 'episode_toplist.html'

    def get_context_data(self, num=100):
        context = super(EpisodeToplistView, self).get_context_data()

        entries = Episode.objects.all()\
                                 .select_related('podcast')\
                                 .prefetch_related('slugs', 'podcast__slugs')\
                                 .toplist(self.language())[:num]
        context['entries'] = entries

        # Determine maximum listener amount (or 0 if no entries exist)
        listeners = [e.listeners for e in entries if e.listeners is not None]
        max_listeners = max(listeners, default=0)
        context['max_listeners'] = max_listeners

        return context


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
            'podcastlists': self.get_random_list(),
            'random_podcast': Podcast.objects.all().random().first(),
            'podcast_ad': Podcast.objects.get_advertised_podcast(),
            })


    def get_random_list(self, podcasts_per_list=5):
        random_list = PodcastList.objects.order_by('?').first()
        yield random_list


@cache_control(private=True)
@vary_on_cookie
def category(request, category, page_size=20):
    try:
        category = Category.objects.get(tags__tag=category)
    except Category.DoesNotExist:
        return HttpResponseNotFound()

    podcasts = category.entries.all()\
                               .prefetch_related('podcast', 'podcast__slugs')

    paginator = Paginator(podcasts, page_size)

    page = request.GET.get('page')
    try:
        podcasts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        podcasts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        podcasts = paginator.page(paginator.num_pages)

    page_list = get_page_list(1, paginator.num_pages, podcasts.number, 15)

    return render(request, 'category.html', {
        'entries': podcasts,
        'category': category.title,
        'page_list': page_list,
        })



RESULTS_PER_PAGE=20

@cache_control(private=True)
@vary_on_cookie
def search(request, template='search.html', args={}):

    if 'q' in request.GET:
        q = request.GET.get('q', '')

        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1

        start = RESULTS_PER_PAGE*(page-1)
        results = search_podcasts(q)
        total = len(results)
        num_pages = int(ceil(total / RESULTS_PER_PAGE))
        results = results[start:start+RESULTS_PER_PAGE]

        page_list = get_page_list(1, num_pages, page, 15)

    else:
        results = []
        q = None
        page_list = []

    max_subscribers = max([p.subscribers for p in results] + [0])

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
def podcast_lists(request, page_size=20):

    lists = PodcastList.objects.all()\
                               .annotate(num_votes=Count('votes'))\
                               .order_by('-num_votes')

    paginator = Paginator(lists, page_size)

    page = request.GET.get('page')
    try:
        lists = paginator.page(page)
    except PageNotAnInteger:
        lists = paginator.page(1)
        page = 1
    except EmptyPage:
        lists = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    num_pages = int(ceil(PodcastList.objects.count() / float(page_size)))
    page_list = get_page_list(1, num_pages, int(page), 15)

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
            try:
                podcast = Podcast.objects.get(urls__url=url)
                can_add = False

            except Podcast.DoesNotExist:
                # check if we could add a podcast for the given URL
                podcast = False
                try:
                    can_add = verify_podcast_url(url)

                except (UpdatePodcastException, NoEpisodesException) as ex:
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

        except (UpdatePodcastException, NoEpisodesException) as ex:
            messages.error(request, str(ex))
            podcast = None

        return self.render_to_response({
                'ready': True,
                'podcasts': podcasts,
            })


class PodcastListView(ListView):
    """ A generic podcast list view """

    paginate_by = 15
    context_object_name = 'podcasts'

    @method_decorator(vary_on_cookie)
    @method_decorator(cache_control(private=True))
    def dispatch(self, *args, **kwargs):
        """ Only used for applying decorators """
        return super(PodcastListView, self).dispatch(*args, **kwargs)

    @property
    def _page(self):
        """ The current page

        There seems to be no other pre-defined method for getting the current
        page, see
        https://docs.djangoproject.com/en/dev/ref/class-based-views/mixins-multiple-object/#multipleobjectmixin
        """
        return self.get_context_data()['page_obj']

    def page_list(self, page_size=15):
        """ Return a list of pages, eg [1, 2, 3, '...', 6, 7, 8] """
        page = self._page
        return get_page_list(1,
                             page.paginator.num_pages,
                             page.number,
                             page.paginator.per_page,
                            )

    def max_subscribers(self):
        """ Maximum subscribers of the podcasts on this page """
        page = self._page
        podcasts = page.object_list
        return max([p.subscriber_count() for p in podcasts] + [0])


class FlattrPodcastList(PodcastListView):
    """ Lists podcasts that have Flattr payment URLs """

    template_name = 'flattr-podcasts.html'

    def get_queryset(self):
        return Podcast.objects.all().flattr()

    def get_context_data(self, num=100):
        context = super(FlattrPodcastList, self).get_context_data()
        context['flattr_auth'] = (self.request.user.is_authenticated
                   #  and bool(self.request.user.get_wksetting(FLATTR_TOKEN))
                        )
        return context


class LicensePodcastList(PodcastListView):
    """ Lists podcasts with a given license """

    template_name = 'directory/license-podcasts.html'

    def get_queryset(self):
        return Podcast.objects.all().license(self.license_url)

    @property
    def license_url(self):
        return self.kwargs['license_url']


class LicenseList(TemplateView):
    """ Lists all podcast licenses """

    template_name = 'directory/licenses.html'

    def licenses(self):
        """ Returns all podcast licenses """
        query = Podcast.objects.exclude(license__isnull=True)
        values = query.values("license").annotate(Count("id")).order_by()

        counter = Counter({l['license']: l['id__count'] for l in values})
        return counter.most_common()
