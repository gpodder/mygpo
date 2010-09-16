from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from mygpo.api.models import Podcast, Episode, EpisodeAction, PodcastGroup
from django.contrib.auth.decorators import login_required
from mygpo.publisher.models import PodcastPublisher
from mygpo.publisher.auth import require_publisher, is_publisher
from mygpo.publisher.forms import SearchPodcastForm, EpisodeForm, PodcastForm
from mygpo.publisher.utils import listener_data, episode_listener_data, check_publisher_permission, episode_list, subscriber_data, device_stats, episode_heatmap
from django.contrib.sites.models import Site
from mygpo.data.feeddownloader import update_podcasts
from mygpo.decorators import requires_token, allowed_methods
from mygpo.web.models import SecurityToken
from django.contrib.auth.models import User


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
            'site': site
            }, context_instance=RequestContext(request))


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
@allowed_methods(['GET', 'POST'])
def podcast(request, id):
    p = get_object_or_404(Podcast, pk=id)

    if not check_publisher_permission(request.user, p):
        return HttpResponseForbidden()

    timeline_data = listener_data([p])
    subscription_data = subscriber_data([p])
    device_data = device_stats([p])

    if request.method == 'POST':
        form = PodcastForm(request.POST, instance=p)
        if form.is_valid():
            form.save()

    elif request.method == 'GET':
        form = PodcastForm(instance=p)

    update_token, c = SecurityToken.objects.get_or_create(user=request.user, object='published_feeds', action='update')

    if 'new_token' in request.GET:
        update_token.random_token()
        update_token.save()

    site = Site.objects.get_current()

    return render_to_response('publisher/podcast.html', {
        'site': site,
        'podcast': p,
        'form': form,
        'timeline_data': timeline_data,
        'subscriber_data': subscription_data,
        'device_data': device_data,
        'update_token': update_token,
        }, context_instance=RequestContext(request))


@require_publisher
def group(request, group_id):
    g = get_object_or_404(PodcastGroup, id=group_id)

    # users need to have publisher access for at least one of the group's podcasts
    if not any([check_publisher_permission(request.user, p) for p in g.podcasts()]):
        return HttpResponseForbidden()


    timeline_data = listener_data(g.podcasts())
    subscription_data = subscriber_data(g.podcasts())
    device_data = device_stats(g.podcasts())

    return render_to_response('publisher/group.html', {
        'group': g,
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


@requires_token(object='published_feeds', action='update')
def update_published_podcasts(request, username):
    user = get_object_or_404(User, username=username)

    published_podcasts = [p.podcast for p in PodcastPublisher.objects.filter(user=user)]
    update_podcasts(published_podcasts)

    return HttpResponse('Updated:\n' + '\n'.join([p.url for p in published_podcasts]), mimetype='text/plain')


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
@allowed_methods(['GET', 'POST'])
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

    timeline_data = episode_listener_data(e)
    heatmap_data, part_length = episode_heatmap(e)

    return render_to_response('publisher/episode.html', {
        'episode': e,
        'form': form,
        'timeline_data': timeline_data,
        'heatmap_data': heatmap_data if any([x > 1 for x in heatmap_data]) else None,
        'heatmap_part_length': part_length,
        }, context_instance=RequestContext(request))


def link(request):
    current_site = Site.objects.get_current()
    return render_to_response('link.html', {
        'url': current_site
        }, context_instance=RequestContext(request))


def advertise(request):
    site = Site.objects.get_current()
    return render_to_response('publisher/advertise.html', {
        'site': site
    }, context_instance=RequestContext(request))

