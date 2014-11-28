import re
import socket
from itertools import count, chain
from collections import Counter
from datetime import datetime

import django
from django.shortcuts import render
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.sites.models import RequestSite
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.conf import settings
from django.contrib.auth import get_user_model

from mygpo.podcasts.models import Podcast, Episode
from mygpo.administration.auth import require_staff
from mygpo.administration.group import PodcastGrouper
from mygpo.maintenance.merge import PodcastMerger, IncorrectMergeException
from mygpo.administration.clients import UserAgentStats, ClientStats
from mygpo.administration.tasks import merge_podcasts
from mygpo.utils import get_git_head
from mygpo.users.models import UserProxy
from mygpo.publisher.models import PublishedPodcast
from mygpo.api.httpresponse import JsonResponse
from mygpo.celery import celery


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

        i = celery.control.inspect()
        scheduled = i.scheduled()
        if not scheduled:
            num_celery_tasks = None
        else:
            num_celery_tasks = sum(len(node) for node in scheduled.values())

        feed_queue_status = self._get_feed_queue_status()

        return self.render_to_response({
            'git_commit': commit,
            'git_msg': msg,
            'base_dir': base_dir,
            'hostname': hostname,
            'django_version': django_version,
            'num_celery_tasks': num_celery_tasks,
            'feed_queue_status': feed_queue_status,
        })

    def _get_feed_queue_status(self):
        now = datetime.utcnow()
        next_podcast = Podcast.objects.order_by_next_update().first()

        delta = (next_podcast.next_update - now)
        delta_mins = delta.total_seconds() / 60
        return delta_mins


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

            p = Podcast.objects.get(urls__url=podcast_url)
            podcasts.append(p)

        return podcasts


class MergeVerify(MergeBase):

    template_name = 'admin/merge-grouping.html'

    def post(self, request):

        try:
            podcasts = self._get_podcasts(request)

            grouper = PodcastGrouper(podcasts)

            get_features = lambda (e_id, e): ((e.url, e.title), e_id)

            num_groups = grouper.group(get_features)


        except InvalidPodcast as ip:
            messages.error(request,
                    _('No podcast with URL {url}').format(url=str(ip)))

            podcasts = []
            num_groups = []

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

        get_features = lambda (e_id, e): (features.get(e_id, e_id), e_id)

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

    template_name = 'admin/task-status.html'

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

        return self.render_to_response({
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
            'podcasts': Podcast.objects.count_fast(),
            'episodes': Episode.objects.count_fast(),
            'users': UserProxy.objects.count_fast(),
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


class ActivateUserView(AdminView):
    """ Lets admins manually activate users """

    template_name = 'admin/activate-user.html'

    def get(self, request):
        return self.render_to_response({})

    def post(self, request):

        username = request.POST.get('username')
        email = request.POST.get('email')

        if not (username or email):
            messages.error(request,
                           _('Provide either username or email address'))
            return HttpResponseRedirect(reverse('admin-activate-user'))

        try:
            user = UserProxy.objects.by_username_or_email(username, email)
        except UserProxy.DoesNotExist:
            messages.error(request, _('No user found'))
            return HttpResponseRedirect(reverse('admin-activate-user'))

        user.activate()
        messages.success(request,
                         _('User {username} ({email}) activated'.format(
                            username=user.username, email=user.email)))
        return HttpResponseRedirect(reverse('admin-activate-user'))



class MakePublisherInput(AdminView):
    """ Get all information necessary for making someone publisher """

    template_name = 'admin/make-publisher-input.html'


class MakePublisher(AdminView):
    """ Assign publisher permissions """

    template_name = 'admin/make-publisher-result.html'

    def post(self, request):
        User = get_user_model()
        username = request.POST.get('username')
        user = User.objects.get(username=username)
        if user is None:
            messages.error(request, 'User "{username}" not found'.format(username=username))
            return HttpResponseRedirect(reverse('admin-make-publisher-input'))

        feeds = request.POST.get('feeds')
        feeds = feeds.split()
        podcasts = set()

        for feed in feeds:
            try:
                podcast = Podcast.objects.get(urls__url=feed)
            except Podcast.DoesNotExist:
                messages.warning(request, 'Podcast with URL {feed} not found'.format(feed=feed))
                continue

            podcasts.add(podcast)

        created, existed = self.set_publisher(request, user, podcasts)

        if (created + existed) > 0:
            self.send_mail(request, user, podcasts)
        return HttpResponseRedirect(reverse('admin-make-publisher-result'))

    def set_publisher(self, request, user, podcasts):
        created, existed = PublishedPodcast.objects.publish_podcasts(user,
                                                                     podcasts)
        messages.success(request,
                         'Set publisher permissions for {created} podcasts; '
                         '{existed} already existed'.format(created=created,
                                                            existed=existed))
        return created, existed

    def send_mail(self, request, user, podcasts):
        site = RequestSite(request)
        msg = render_to_string('admin/make-publisher-mail.txt', {
                'user': user,
                'podcasts': podcasts,
                'support_url': settings.SUPPORT_URL,
                'site': site,
            },
            context_instance=RequestContext(request))
        subj = get_email_subject(site, _('Publisher Permissions'))

        user.email_user(subj, msg)
        messages.success(request, 'Sent email to user "{username}"'.format(username=user.username))


class MakePublisherResult(AdminView):
    template_name = 'make-publisher-result.html'


def get_email_subject(site, txt):
    return '[{domain}] {txt}'.format(domain=site.domain, txt=txt)
