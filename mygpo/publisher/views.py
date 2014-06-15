from functools import wraps
import urllib

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponseForbidden, Http404
from django.core.cache import cache
from django.views.decorators.cache import never_cache, cache_control
from django.views.decorators.vary import vary_on_cookie
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib import messages

from mygpo.core.proxy import proxy_object
from mygpo.publisher.auth import require_publisher, is_publisher
from mygpo.publisher.forms import SearchPodcastForm
from mygpo.publisher.utils import listener_data, episode_listener_data, \
         check_publisher_permission, subscriber_data
from mygpo.web.heatmap import EpisodeHeatmap
from mygpo.web.views.episode import oldid_decorator, slug_id_decorator
from mygpo.web.views.podcast import \
         slug_id_decorator as podcast_slug_id_decorator, \
         oldid_decorator as podcast_oldid_decorator
from mygpo.web.utils import get_podcast_link_target, normalize_twitter, \
     get_episode_link_target
from django.contrib.sites.models import RequestSite
from mygpo.data.tasks import update_podcasts
from mygpo.decorators import requires_token, allowed_methods
from mygpo.users.models import User
from mygpo.db.couchdb.episode import episodes_for_podcast, episodes_for_slug, \
    set_episode_slug, remove_episode_slug
from mygpo.db.couchdb.podcast import podcast_by_id, podcasts_by_id, \
         podcast_for_url, podcastgroup_by_id, update_additional_data
from mygpo.db.couchdb.episode_state import episode_listener_counts
from mygpo.db.couchdb.pubsub import subscription_for_topic


@vary_on_cookie
@cache_control(private=True)
def home(request):
    if is_publisher(request.user):
        podcasts = podcasts_by_id(request.user.published_objects)
        site = RequestSite(request)
        update_token = request.user.get_token('publisher_update_token')
        form = SearchPodcastForm()
        return render(request, 'publisher/home.html', {
            'update_token': update_token,
            'podcasts': podcasts,
            'form': form,
            'site': site,
            })

    else:
        site = RequestSite(request)
        return render(request, 'publisher/info.html', {
            'site': site
            })


@vary_on_cookie
@cache_control(private=True)
@require_publisher
def search_podcast(request):
    form = SearchPodcastForm(request.POST)
    if form.is_valid():
        url = form.cleaned_data['url']

        podcast = podcast_for_url(url)
        if not podcast:
            raise Http404

        url = get_podcast_link_target(podcast, 'podcast-publisher-detail')
    else:
        url = reverse('publisher')

    return HttpResponseRedirect(url)


@vary_on_cookie
@cache_control(private=True)
@require_publisher
@allowed_methods(['GET', 'POST'])
def podcast(request, podcast):

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    timeline_data = listener_data([podcast])
    subscription_data = subscriber_data([podcast])[-20:]

    if podcast.group:
        group = podcastgroup_by_id(podcast.group)
    else:
        group = None

    update_token = request.user.publisher_update_token

    heatmap = EpisodeHeatmap(podcast.get_id())

    pubsubscription = subscription_for_topic(podcast.url)

    site = RequestSite(request)
    feedurl_quoted = urllib.quote(podcast.url)

    return render(request, 'publisher/podcast.html', {
        'site': site,
        'podcast': podcast,
        'group': group,
        'form': None,
        'timeline_data': timeline_data,
        'subscriber_data': subscription_data,
        'update_token': update_token,
        'heatmap': heatmap,
        'feedurl_quoted': feedurl_quoted,
        'pubsubscription': pubsubscription,
        })


@vary_on_cookie
@cache_control(private=True)
@require_publisher
def group(request, group):

    podcasts = group.podcasts

    # users need to have publisher access for at least one of the group's podcasts
    if not any([check_publisher_permission(request.user, p) for p in podcasts]):
        return HttpResponseForbidden()

    timeline_data = listener_data(podcasts)
    subscription_data = list(subscriber_data(podcasts))[-20:]

    return render(request, 'publisher/group.html', {
        'group': group,
        'timeline_data': timeline_data,
        'subscriber_data': subscription_data,
        })


@vary_on_cookie
@cache_control(private=True)
@require_publisher
def update_podcast(request, podcast):

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    update_podcasts.delay([podcast.url])
    messages.success(request, _('The update has been scheduled. It might take some time until the results are visible.'))

    url = get_podcast_link_target(podcast, 'podcast-publisher-detail')
    return HttpResponseRedirect(url)


@vary_on_cookie
@cache_control(private=True)
@require_publisher
def save_podcast(request, podcast):
    twitter = normalize_twitter(request.POST.get('twitter', ''))
    update_additional_data(podcast, twitter)
    messages.success(request, _('Data updated'))
    url = get_podcast_link_target(podcast, 'podcast-publisher-detail')
    return HttpResponseRedirect(url)



@never_cache
@require_publisher
def new_update_token(request, username):
    request.user.create_new_token('publisher_update_token')
    request.user.save()
    messages.success(request, _('Publisher token updated'))
    return HttpResponseRedirect(reverse('publisher'))


@never_cache
@requires_token(token_name='publisher_update_token')
def update_published_podcasts(request, username):
    user = User.get_user(username)
    if not user:
        raise Http404

    published_podcasts = podcasts_by_id(user.published_objects)
    update_podcasts.delay([podcast.url for podcast in published_podcasts])
    return HttpResponse('Updated:\n' + '\n'.join([p.url for p in published_podcasts]), mimetype='text/plain')


@vary_on_cookie
@cache_control(private=True)
@require_publisher
def episodes(request, podcast):

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    episodes = episodes_for_podcast(podcast, descending=True)
    listeners = dict(episode_listener_counts(podcast))

    max_listeners = max(listeners.values() + [0])

    def annotate_episode(episode):
        listener_count = listeners.get(episode._id, None)
        return proxy_object(episode, listeners=listener_count)

    episodes = map(annotate_episode, episodes)

    return render(request, 'publisher/episodes.html', {
        'podcast': podcast,
        'episodes': episodes,
        'max_listeners': max_listeners
        })


@require_publisher
@vary_on_cookie
@cache_control(private=True)
@allowed_methods(['GET', 'POST'])
def episode(request, episode):

    site = RequestSite(request)
    podcast = podcast_by_id(episode.podcast)

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = None  # EpisodeForm(request.POST, instance=e)
        # if form.is_valid():
        #    form.save()

    elif request.method == 'GET':
        form = None  # EpisodeForm(instance=e)

    timeline_data = list(episode_listener_data(episode))

    heatmap = EpisodeHeatmap(episode.podcast, episode._id,
              duration=episode.duration)

    return render(request, 'publisher/episode.html', {
        'is_secure': request.is_secure(),
        'domain': site.domain,
        'episode': episode,
        'podcast': podcast,
        'form': form,
        'timeline_data': timeline_data,
        'heatmap': heatmap,
        })


@require_publisher
@never_cache
@allowed_methods(['POST'])
def update_episode_slug(request, episode):
    """ sets a new "main" slug, and moves the existing to the merged slugs """

    new_slug = request.POST.get('slug')
    podcast = podcast_by_id(episode.podcast)

    if new_slug:
        # remove the new slug from other episodes (of the same podcast)
        other_episodes = episodes_for_slug(podcast.get_id(), new_slug)

        for other_episode in other_episodes:

            if other_episode == episode:
                continue

            remove_episode_slug(other_episode, new_slug)
            messages.warning(request,
                _(u'Removed slug {slug} from {episode}'.format(
                    slug=new_slug, episode=other_episode.title))
            )

    set_episode_slug(episode, new_slug)

    # TODO: we should use better cache invalidation
    cache.clear()

    return HttpResponseRedirect(
        get_episode_link_target(episode, podcast, 'episode-publisher-detail')
    )


@vary_on_cookie
@cache_control(private=True)
def link(request):
    current_site = RequestSite(request)
    return render(request, 'link.html', {
        'url': current_site
        })


@vary_on_cookie
@cache_control(private=True)
def advertise(request):
    site = RequestSite(request)
    return render(request, 'publisher/advertise.html', {
        'site': site
    })


def group_slug_id_decorator(f):
    @wraps(f)
    def _decorator(request, slug_id, *args, **kwargs):
        group = podcastgroup_by_id(slug_id)

        if group is None:
            raise Http404

        return f(request, group, *args, **kwargs)

    return _decorator


episode_oldid        = oldid_decorator(episode)
podcast_oldid        = podcast_oldid_decorator(podcast)
update_podcast_oldid = podcast_oldid_decorator(update_podcast)
save_podcast_oldid   = podcast_oldid_decorator(save_podcast)
episodes_oldid       = podcast_oldid_decorator(episodes)

episode_slug_id        = slug_id_decorator(episode)
update_episode_slug_slug_id = slug_id_decorator(update_episode_slug)
podcast_slug_id        = podcast_slug_id_decorator(podcast)
episodes_slug_id       = podcast_slug_id_decorator(episodes)
update_podcast_slug_id = podcast_slug_id_decorator(update_podcast)
save_podcast_slug_id   = podcast_slug_id_decorator(save_podcast)
group_slug_id          = group_slug_id_decorator(group)
