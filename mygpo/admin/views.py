import re

from django.shortcuts import render

from mygpo.admin.auth import require_staff
from mygpo.admin.group import PodcastGrouper
from mygpo.core.models import Podcast
from mygpo.counter import Counter
from mygpo.maintenance.merge import PodcastMerger


@require_staff
def overview(request):
    return render(request, 'admin/overview.html', {
        })


@require_staff
def merge_select(request):
    return render(request, 'admin/merge-select.html', {
        })


@require_staff
def merge_verify(request):
    podcast1 = Podcast.for_url(request.POST['feed1'])
    podcast2 = Podcast.for_url(request.POST['feed2'])

    grouper = PodcastGrouper(podcast1, podcast2)

    get_features = lambda (e_id, e): ((e.url, e.title), e_id)

    num_groups = grouper.group(get_features)

    return render(request, 'admin/merge-grouping.html', {
            'podcast1': podcast1,
            'podcast2': podcast2,
            'groups': num_groups,
        })


RE_EPISODE = re.compile(r'episode_([0-9a-fA-F]{32})')

@require_staff
def merge_process(request):

    podcast1 = Podcast.for_url(request.POST['feed1'])
    podcast2 = Podcast.for_url(request.POST['feed2'])

    grouper = PodcastGrouper(podcast1, podcast2)

    features = {}
    for key, feature in request.POST.items():
        m = RE_EPISODE.match(key)
        if m:
            episode_id = m.group(1)
            features[episode_id] = feature

    get_features = lambda (e_id, e): (features[e_id], e_id)

    num_groups = grouper.group(get_features)

    if 'renew' in request.POST:
        return render(request, 'admin/merge-grouping.html', {
                'podcast1': podcast1,
                'podcast2': podcast2,
                'groups': num_groups,
            })


    elif 'merge' in request.POST:

        actions = Counter()

        # merge podcast, reassign episodes
        pm = PodcastMerger(podcast1, podcast2, actions, num_groups)
        pm.merge()

        return render(request, 'admin/merge-finished.html', {
                'actions': actions.items(),
                'podcast': podcast1,
            })
