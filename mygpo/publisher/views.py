from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponseForbidden, Http404
from django.views.decorators.cache import cache_page
from mygpo.core import models
from mygpo.core.proxy import proxy_object
from mygpo.api.models import Podcast, PodcastGroup
from mygpo.publisher.auth import require_publisher, is_publisher
from mygpo.publisher.forms import SearchPodcastForm, PodcastForm
from mygpo.publisher.utils import listener_data, episode_listener_data, check_publisher_permission, subscriber_data
from mygpo.web.heatmap import EpisodeHeatmap
from mygpo.web.views.episode import oldid_decorator, slug_id_decorator
from mygpo.web.views.podcast import \
         slug_id_decorator as podcast_slug_id_decorator
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

    podcast = migrate.get_or_migrate_podcast(p)
    episodes = podcast.get_episodes(descending=True)
    listeners = dict(podcast.episode_listener_counts())

    max_listeners = max(listeners.values() + [0])

    def annotate_episode(episode):
        listener_count = listeners.get(episode._id, None)
        return proxy_object(episode, listeners=listener_count)

    episodes = map(annotate_episode, episodes)

    return render_to_response('publisher/episodes.html', {
        'podcast': podcast,
        'episodes': episodes,
        'max_listeners': max_listeners
        }, context_instance=RequestContext(request))


@require_publisher
@allowed_methods(['GET', 'POST'])
def episode(request, episode):

    podcast = models.Podcast.get(episode.podcast)
    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = None #EpisodeForm(request.POST, instance=e)
        #if form.is_valid():
        #    form.save()

    elif request.method == 'GET':
        form = None #EpisodeForm(instance=e)

    timeline_data = episode_listener_data(episode)

    heatmap = EpisodeHeatmap(episode.podcast, episode._id,
              duration=episode.duration)

    return render_to_response('publisher/episode.html', {
        'episode': episode,
        'podcast': podcast,
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


episode_oldid = oldid_decorator(episode)

episode_slug_id        = slug_id_decorator(episode)
podcast_slug_id        = podcast_slug_id_decorator(podcast)
episodes_slug_id       = podcast_slug_id_decorator(episodes)
update_podcast_slug_id = podcast_slug_id_decorator(update_podcast)
