from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.cache import never_cache, cache_control
from django.views.decorators.vary import vary_on_cookie
from django.contrib.auth.decorators import login_required

from mygpo.users.models import Client
from mygpo.history.models import HistoryEntry
from mygpo.podcasts.views import slug_decorator, id_decorator
from mygpo.api import APIView

class History(APIView):
    @vary_on_cookie
    @cache_control(private=True)
    @login_required
    def history(self, request, count=15, uid=None):
        user = request.user
        client = None

        history = HistoryEntry.objects.filter(user=user)\
                                      .select_related('podcast', 'episode')

        if uid:
            try:
                client = user.client_set.get(uid=uid)
            except Client.DoesNotExist as e:
                messages.error(request, str(e))

        # if a client was given, filter for it
        if client:
            history = history.filter(client=client)

        paginator = Paginator(history, count)

        page = request.GET.get('page')

        try:
            entries = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            entries = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            entries = paginator.page(paginator.num_pages)

        return {
            'history': entries,
            'client': client,
            'page': page,
        }


class PodcastHistory(APIView):
    @never_cache
    @login_required
    def get(self, request, podcast):
        """ shows the subscription history of the user """
        user = request.user
        history = HistoryEntry.objects.filter(user=request.user, podcast=podcast)

        return {
            'history': history,
            'podcast': podcast,
        }
