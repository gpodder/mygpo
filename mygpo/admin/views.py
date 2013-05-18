import re
import socket
from itertools import count
from collections import Counter

import django
from django.shortcuts import render
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.conf import settings

from mygpo.admin.auth import require_staff
from mygpo.admin.group import PodcastGrouper
from mygpo.maintenance.merge import PodcastMerger, IncorrectMergeException
from mygpo.users.models import User
from mygpo.admin.clients import UserAgentStats, ClientStats
from mygpo.admin.tasks import merge_podcasts
from mygpo.utils import get_git_head
from mygpo.api.httpresponse import JsonResponse
from mygpo.cel import celery
from mygpo.db.couchdb import get_main_database
from mygpo.db.couchdb.episode import episode_count, filetype_stats
from mygpo.db.couchdb.podcast import podcast_count, podcast_for_url


class InvalidPodcast(Exception):
    """ raised when we try to merge a podcast that doesn't exist """

class AdminView(TemplateView):

    @method_decorator(require_staff)
    def dispatch(self, *args, **kwargs):
        return super(AdminView, self).dispatch(*args, **kwargs)


class Overview(AdminView):
    template_name = 'admin/overview.html'


class HostInfo(AdminView):
    """ shows host information for diagnosis """

    template_name = 'admin/hostinfo.html'

    def get(self, request):
        commit, msg = get_git_head()
        base_dir = settings.BASE_DIR
        hostname = socket.gethostname()
        django_version = django.VERSION

        main_db = get_main_database()

        db_tasks = main_db.server.active_tasks()

        i = celery.control.inspect()
        num_celery_tasks = len(i.scheduled() or [])

        return self.render_to_response({
            'git_commit': commit,
            'git_msg': msg,
            'base_dir': base_dir,
            'hostname': hostname,
            'django_version': django_version,
            'main_db': main_db.uri,
            'db_tasks': db_tasks,
            'num_celery_tasks': num_celery_tasks,
        })



class MergeSelect(AdminView):
    template_name = 'admin/merge-select.html'

    def get(self, request):
        num = int(request.GET.get('podcasts', 2))
        urls = [''] * num

        return self.render_to_response({
                'urls': urls,
            })


class MergeBase(AdminView):

    def _get_podcasts(self, request):
        podcasts = []
        for n in count():
            podcast_url = request.POST.get('feed%d' % n, None)
            if podcast_url is None:
                break

            if not podcast_url:
                continue

            podcast = podcast_for_url(podcast_url)

            if not podcast:
                raise InvalidPodcast(podcast_url)

            podcasts.append(podcast_for_url(podcast_url))

        return podcasts


class MergeVerify(MergeBase):

    template_name = 'admin/merge-grouping.html'

    def post(self, request):

        try:
            podcasts = self._get_podcasts(request)

        except InvalidPodcast as ip:
            messages.error(request,
                    _('No podcast with URL {url}').format(url=str(ip)))

        grouper = PodcastGrouper(podcasts)

        get_features = lambda (e_id, e): ((e.url, e.title), e_id)

        num_groups = grouper.group(get_features)

        return self.render_to_response({
                'podcasts': podcasts,
                'groups': num_groups,
            })


class MergeProcess(MergeBase):

    RE_EPISODE = re.compile(r'episode_([0-9a-fA-F]{32})')

    def post(self, request):

        try:
            podcasts = self._get_podcasts(request)

        except InvalidPodcast as ip:
            messages.error(request,
                    _('No podcast with URL {url}').format(url=str(ip)))

        grouper = PodcastGrouper(podcasts)

        features = {}
        for key, feature in request.POST.items():
            m = self.RE_EPISODE.match(key)
            if m:
                episode_id = m.group(1)
                features[episode_id] = feature

        get_features = lambda (e_id, e): (features[e_id], e_id)

        num_groups = grouper.group(get_features)

        if 'renew' in request.POST:
            return render(request, 'admin/merge-grouping.html', {
                    'podcasts': podcasts,
                    'groups': num_groups,
                })


        elif 'merge' in request.POST:

            podcast_ids = [p.get_id() for p in podcasts]
            num_groups = list(num_groups)

            res = merge_podcasts.delay(podcast_ids, num_groups)

            return HttpResponseRedirect(reverse('admin-merge-status',
                        args=[res.task_id]))


class MergeStatus(AdminView):
    """ Displays the status of the merge operation """

    template_name = 'admin/merge-status.html'

    def get(self, request, task_id):
        result = merge_podcasts.AsyncResult(task_id)

        if not result.ready():
            return self.render_to_response({
                'ready': False,
            })

        # clear cache to make merge result visible
        # TODO: what to do with multiple frontends?
        cache.clear()

        try:
            actions, podcast = result.get()

        except IncorrectMergeException as ime:
            messages.error(request, str(ime))
            return HttpResponseRedirect(reverse('admin-merge'))

        return render(request, 'admin/merge-status.html', {
                'ready': True,
                'actions': actions.items(),
                'podcast': podcast,
            })



class UserAgentStatsView(AdminView):
    template_name = 'admin/useragents.html'

    def get(self, request):

        uas = UserAgentStats()
        useragents = uas.get_entries()

        return self.render_to_response({
                'useragents': useragents.most_common(),
                'max_users': uas.max_users,
                'total': uas.total_users,
            })


class ClientStatsView(AdminView):
    template_name = 'admin/clients.html'

    def get(self, request):

        cs = ClientStats()
        clients = cs.get_entries()

        return self.render_to_response({
                'clients': clients.most_common(),
                'max_users': cs.max_users,
                'total': cs.total_users,
            })


class ClientStatsJsonView(AdminView):
    def get(self, request):

        cs = ClientStats()
        clients = cs.get_entries()

        return JsonResponse(map(self.to_dict, clients.most_common()))

    def to_dict(self, res):
        obj, count = res

        if not isinstance(obj, tuple):
            return obj, count

        return obj._asdict(), count


class StatsView(AdminView):
    """ shows general stats as HTML page """

    template_name = 'admin/stats.html'

    def _get_stats(self):
        return {
            'podcasts': podcast_count(),
            'episodes': episode_count(),
            'users': User.count(),
        }

    def get(self, request):
        stats = self._get_stats()
        return self.render_to_response({
            'stats': stats,
        })


class StatsJsonView(StatsView):
    """ provides general stats as JSON """

    def get(self, request):
        stats = self._get_stats()
        return JsonResponse(stats)


class FiletypeStatsView(AdminView):

    template_name = 'admin/filetypes.html'

    def get(self, request):
        stats = filetype_stats()

        if len(stats):
            max_num = stats.most_common(1)[0][1]
        else:
            max_num = 0

        return self.render_to_response({
            'max_num': max_num,
            'stats': stats.most_common(),
        })
