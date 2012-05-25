import re
from itertools import count

from django.shortcuts import render
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from mygpo.admin.auth import require_staff
from mygpo.admin.group import PodcastGrouper
from mygpo.core.models import Podcast
from mygpo.counter import Counter
from mygpo.maintenance.merge import PodcastMerger, IncorrectMergeException


class AdminView(TemplateView):

    @method_decorator(require_staff)
    def dispatch(self, *args, **kwargs):
        return super(AdminView, self).dispatch(*args, **kwargs)


class Overview(AdminView):
    template_name = 'admin/overview.html'


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

            podcast = Podcast.for_url(podcast_url)

            if not podcast:
                raise InvalidPodcast(podcast_url)

            podcasts.append(Podcast.for_url(podcast_url))

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

            actions = Counter()

            try:
                # merge podcast, reassign episodes
                pm = PodcastMerger(podcasts, actions, num_groups)
                pm.merge()

            except IncorrectMergeException as ime:
                messages.error(request, str(ime))
                return HttpResponseRedirect(reverse('admin-merge'))

            return render(request, 'admin/merge-finished.html', {
                    'actions': actions.items(),
                    'podcast': podcasts,
                })
