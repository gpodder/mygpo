from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from mygpo.api.models import Podcast, Episode, EpisodeAction
from mygpo.api.constants import DEVICE_TYPES
from django.contrib.auth.decorators import login_required
from mygpo.publisher.models import PodcastPublisher
from mygpo.publisher.auth import require_publisher, is_publisher
from mygpo.publisher.forms import SearchPodcastForm, EpisodeForm, PodcastForm
from mygpo.publisher.utils import listener_data, check_publisher_permission, episode_list, subscriber_data
from django.contrib.sites.models import Site
from mygpo.data.feeddownloader import update_podcasts


def home(request):
    if is_publisher(request.user):
        podcasts = [x.podcast for x in PodcastPublisher.objects.filter(user=request.user)]
        form = SearchPodcastForm()
        return render_to_response('publisher/home.html', {
            'podcasts': podcasts,
            'form': form
            }, context_instance=RequestContext(request))

    else:
        site = Site.objects.get_current()
        return render_to_response('publisher/info.html', {
            'site': site})


@require_publisher
def search_podcast(request):
    form = SearchPodcastForm(request.POST)
    if form.is_valid():
        url = form.cleaned_data['url']
        p = get_object_or_404(Podcast, url=url)

        return HttpResponseRedirect('/publisher/podcast/%d' % p.id)

    else:
        return HttpResponseRedirect('/publisher/')

@require_publisher
def podcast(request, id):
    p = get_object_or_404(Podcast, pk=id)

    if not check_publisher_permission(request.user, p):
        return HttpResponseForbidden()

    timeline_data = listener_data(p)
    subscription_data = subscriber_data(p)
    device_data = device_stats(p)

    if request.method == 'POST':
        form = PodcastForm(request.POST, instance=p)
        if form.is_valid():
            form.save()

    elif request.method == 'GET':
        form = PodcastForm(instance=p)

    return render_to_response('publisher/podcast.html', {
        'podcast': p,
        'form': form,
        'timeline_data': timeline_data,
        'subscriber_data': subscription_data,
        'device_data': device_data,
        }, context_instance=RequestContext(request))


@require_publisher
def update_podcast(request, id):
    p = get_object_or_404(Podcast, pk=id)

    if not check_publisher_permission(request.user, p):
        return HttpResponseForbidden()

    update_podcasts( [p] )

    return HttpResponseRedirect('/publisher/podcast/%s' % id)


@require_publisher
def episodes(request, id):
    p = get_object_or_404(Podcast, pk=id)

    if not check_publisher_permission(request.user, p):
        return HttpResponseForbidden()

    episodes = episode_list(p)
    max_listeners = max([x.listeners for x in episodes]) if len(episodes) else 0

    return render_to_response('publisher/episodes.html', {
        'podcast': p,
        'episodes': episodes,
        'max_listeners': max_listeners
        }, context_instance=RequestContext(request))


@require_publisher
def episode(request, id):
    e = get_object_or_404(Episode, pk=id)

    if not check_publisher_permission(request.user, e.podcast):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = EpisodeForm(request.POST, instance=e)
        if form.is_valid():
            form.save()

    elif request.method == 'GET':
        form = EpisodeForm(instance=e)

    return render_to_response('publisher/episode.html', {
        'episode': e,
        'form': form
        }, context_instance=RequestContext(request))


def device_stats(podcast):
    res = {}
    for type in DEVICE_TYPES:
        c = EpisodeAction.objects.filter(episode__podcast=podcast, device__type=type[0]).values('user_id').distinct().count()
        if c > 0:
            res[type[1]] = c

    return res

