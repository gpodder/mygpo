from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.views.decorators.cache import cache_page
from mygpo.core import models
from mygpo.api.models import Podcast, PodcastGroup
from mygpo.publisher.auth import require_publisher, is_publisher
from mygpo.publisher.forms import SearchPodcastForm, PodcastForm
from mygpo.publisher.utils import listener_data, episode_listener_data, check_publisher_permission, subscriber_data
from mygpo.web.heatmap import EpisodeHeatmap
from django.contrib.sites.models import RequestSite
from mygpo.data.feeddownloader import update_podcasts
from mygpo.decorators import requires_token, allowed_methods
from django.contrib.auth.models import User
from mygpo import migrate


def home(request):
    if is_publisher(request.user):
        u = migrate.get_or_migrate_user(request.user)
        podcasts = models.Podcast.get_multi(u.published_objects)
        form = SearchPodcastForm()
        return render_to_response('publisher/home.html', {
            'podcasts': podcasts,
            'form': form
            }, context_instance=RequestContext(request))

    else:
        site = RequestSite(request)
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

    new_p = migrate.get_or_migrate_podcast(p)

    timeline_data = listener_data([new_p])
    subscription_data = subscriber_data([new_p])

    if request.method == 'POST':
        form = PodcastForm(request.POST, instance=p)
        if form.is_valid():
            form.save()

    elif request.method == 'GET':
        form = PodcastForm(instance=p)

    user = migrate.get_or_migrate_user(request.user)
    if 'new_token' in request.GET:
        user.create_new_token('publisher_update_token')
        user.save()

    update_token = user.publisher_update_token

    heatmap = EpisodeHeatmap(new_p.get_id())

    site = RequestSite(request)

    return render_to_response('publisher/podcast.html', {
        'site': site,
        'podcast': p,
        'form': form,
        'timeline_data': timeline_data,
        'subscriber_data': subscription_data,
        'update_token': update_token,
        'heatmap': heatmap,
        }, context_instance=RequestContext(request))


@require_publisher
def group(request, group_id):
    g = get_object_or_404(PodcastGroup, id=group_id)

    # users need to have publisher access for at least one of the group's podcasts
    if not any([check_publisher_permission(request.user, p) for p in g.podcasts()]):
        return HttpResponseForbidden()

    new_podcasts = [migrate.get_or_migrate_podcast(p) for p in g.podcasts()]

    timeline_data = listener_data(new_podcasts)
    subscription_data = subscriber_data(new_podcasts)

    return render_to_response('publisher/group.html', {
        'group': g,
        'timeline_data': timeline_data,
        'subscriber_data': subscription_data,
        }, context_instance=RequestContext(request))


@require_publisher
def update_podcast(request, id):
    p = get_object_or_404(Podcast, pk=id)

    if not check_publisher_permission(request.user, p):
        return HttpResponseForbidden()

    update_podcasts( [p] )

    return HttpResponseRedirect('/publisher/podcast/%s' % id)


@requires_token(token_name='publisher_update_token')
def update_published_podcasts(request, username):
    user = get_object_or_404(User, username=username)
    user = migrate.get_or_migrate_user(user)

    published_podcasts = models.Podcast.get_multi(user.published_objects)
    old_podcasts = map(models.Podcast.get_old_obj, published_podcasts)
    update_podcasts(old_podcasts)

    return HttpResponse('Updated:\n' + '\n'.join([p.url for p in published_podcasts]), mimetype='text/plain')


@require_publisher
def episodes(request, id):
    p = get_object_or_404(Podcast, pk=id)

    if not check_publisher_permission(request.user, p):
        return HttpResponseForbidden()

    episodes = p.get_episodes()

    new_podcast = migrate.get_or_migrate_podcast(p)
    new_episodes = dict( (e.oldid, e._id) for e in new_podcast.get_episodes() )

    listeners = dict(new_podcast.episode_listener_counts())

    max_listeners = max(listeners.values() + [0])

    for e in episodes:
        e_id = new_episodes.get(e.id, None)
        if not e_id: continue
        e.listeners = listeners.get(e_id)

    return render_to_response('publisher/episodes.html', {
        'podcast': p,
        'episodes': episodes,
        'max_listeners': max_listeners
        }, context_instance=RequestContext(request))


@require_publisher
@allowed_methods(['GET', 'POST'])
def episode(request, id):
    episode = models.Episode.for_oldid(id)
    if episode is None:
        #TODO: Check
        raise Http404

    # TODO: refactor
    if not check_publisher_permission(request.user, e.podcast):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = None #EpisodeForm(request.POST, instance=e)
        if form.is_valid():
            form.save()

    elif request.method == 'GET':
        form = None #EpisodeForm(instance=e)

    episode = migrate.get_or_migrate_episode(e)

    timeline_data = episode_listener_data(episode)

    heatmap = EpisodeHeatmap(episode.podcast, episode._id,
              duration=episode.duration)

    return render_to_response('publisher/episode.html', {
        'episode': e,
        'form': form,
        'timeline_data': timeline_data,
        'heatmap': heatmap,
        }, context_instance=RequestContext(request))


def link(request):
    current_site = RequestSite(request)
    return render_to_response('link.html', {
        'url': current_site
        }, context_instance=RequestContext(request))


def advertise(request):
    site = RequestSite(request)
    return render_to_response('publisher/advertise.html', {
        'site': site
    }, context_instance=RequestContext(request))

