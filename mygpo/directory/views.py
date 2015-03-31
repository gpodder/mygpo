from __future__ import division

from math import ceil
from collections import Counter

from django.http import HttpResponseNotFound, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.contrib.sites.models import RequestSite
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import ListView
from django.utils.decorators import method_decorator
from django.views.generic.base import View, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import ugettext as _

from feedservice.parse.models import ParserException
from feedservice.parse import FetchFeedException

from mygpo.podcasts.models import Podcast, Episode
from mygpo.web.utils import process_lang_params, get_language_names, \
         get_page_list, sanitize_language_codes
from mygpo.directory.tags import Topics
from mygpo.users.settings import FLATTR_TOKEN
from mygpo.categories.models import Category
from mygpo.podcastlists.models import PodcastList
from mygpo.data.feeddownloader import NoEpisodesException
from mygpo.data.tasks import update_podcasts
from mygpo.api import APIView


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
        context['max_listeners'] = max([0]+[e.listeners for e in entries])

        return context



class DirectoryTopics(APIView):

    def get(self, request):
        return {
            # evaluated lazyly, cached by template
            'topics': Topics(),
        }


class RandomPodcast(APIView):

    def get(self, request):
        return {
            'podcast': Podcast.objects.all().random().first(),
        }


class CategoryView(APIView):
    @cache_control(private=True)
    @vary_on_cookie
    def get(self, request, category, page_size=20):
        category = Category.objects.get(tags__tag=category)

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

        return {
            'entries': podcasts,
            'category': category.title,
            'page_list': page_list,
        }


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


class AddPodcastStatus(APIView):
    """ Status of adding a podcast """

    def get(self, request, task_id):
        result = update_podcasts.AsyncResult(task_id)

        if not result.ready():
            return {
                'task_id': task_id,
                'ready': False,
            }

        try:
            podcasts = result.get()

        except (ParserException, FetchFeedException,
                NoEpisodesException) as ex:
            podcast = None

        return {
                'ready': True,
                'podcasts': podcasts,
        }


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
        context['flattr_auth'] = (self.request.user.is_authenticated()
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


class LicenseList(APIView):
    """ Lists all podcast licenses """

    def get(self, request):
        """ Returns all podcast licenses """
        query = Podcast.objects.exclude(license__isnull=True)
        values = query.values("license").annotate(Count("id")).order_by()

        counter = Counter({l['license']: l['id__count'] for l in values})
        return {
            'licenses': counter.most_common(),
        }
