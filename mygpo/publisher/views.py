from functools import wraps
import urllib.request, urllib.parse, urllib.error

from django.shortcuts import render
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseForbidden,
    Http404,
)
from django.core.cache import cache
from django.views.decorators.cache import never_cache, cache_control
from django.views.decorators.vary import vary_on_cookie
from django.urls import reverse
from django.utils.translation import gettext as _
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from mygpo.podcasts.models import PodcastGroup, Podcast, Episode
from mygpo.publisher.auth import require_publisher, is_publisher
from mygpo.publisher.forms import SearchPodcastForm
from mygpo.publisher.utils import (
    listener_data,
    episode_listener_data,
    check_publisher_permission,
    subscriber_data,
)
from mygpo.podcasts.views.episode import (
    slug_decorator as episode_slug_decorator,
    id_decorator as episode_id_decorator,
)
from mygpo.podcasts.views.podcast import (
    slug_decorator as podcast_slug_decorator,
    id_decorator as podcast_id_decorator,
)
from mygpo.web.utils import (
    get_podcast_link_target,
    normalize_twitter,
    get_episode_link_target,
)
from django.contrib.sites.requests import RequestSite
from mygpo.data.tasks import update_podcasts
from mygpo.data.models import PodcastUpdateResult
from mygpo.decorators import requires_token, allowed_methods
from mygpo.pubsub.models import HubSubscription


@vary_on_cookie
@cache_control(private=True)
def home(request):
    if is_publisher(request.user):
        podcasts = Podcast.objects.filter(
            publishedpodcast__publisher=request.user
        ).prefetch_related("slugs")
        site = RequestSite(request)
        update_token = request.user.profile.get_token("publisher_update_token")
        form = SearchPodcastForm()
        return render(
            request,
            "publisher/home.html",
            {
                "update_token": update_token,
                "podcasts": podcasts,
                "form": form,
                "site": site,
            },
        )

    else:
        site = RequestSite(request)
        return render(request, "publisher/info.html", {"site": site})


@vary_on_cookie
@cache_control(private=True)
@require_publisher
def search_podcast(request):
    form = SearchPodcastForm(request.POST)
    if form.is_valid():
        podcast_url = form.cleaned_data["url"]
        podcast = get_object_or_404(Podcast, urls__url=podcast_url)
        url = get_podcast_link_target(podcast, "podcast-publisher-detail")
    else:
        url = reverse("publisher")

    return HttpResponseRedirect(url)


@vary_on_cookie
@cache_control(private=True)
@require_publisher
@allowed_methods(["GET", "POST"])
def podcast(request, podcast):

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    timeline_data = None  # listener_data([podcast])
    subscription_data = None  # subscriber_data([podcast])[-20:]

    update_token = request.user.profile.get_token("publisher_update_token")

    try:
        pubsubscription = HubSubscription.objects.get(topic_url=podcast.url)
    except HubSubscription.DoesNotExist:
        pubsubscription = None

    MAX_UPDATE_RESULTS = 10

    update_results = PodcastUpdateResult.objects.filter(podcast=podcast)
    update_results = update_results[:MAX_UPDATE_RESULTS]

    site = RequestSite(request)
    feedurl_quoted = urllib.parse.quote(podcast.url.encode("ascii"))

    return render(
        request,
        "publisher/podcast.html",
        {
            "site": site,
            "podcast": podcast,
            "group": podcast.group,
            "form": None,
            "timeline_data": timeline_data,
            "subscriber_data": subscription_data,
            "update_token": update_token,
            "feedurl_quoted": feedurl_quoted,
            "pubsubscription": pubsubscription,
            "update_results": update_results,
        },
    )


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

    return render(
        request,
        "publisher/group.html",
        {
            "group": group,
            "timeline_data": timeline_data,
            "subscriber_data": subscription_data,
        },
    )


@vary_on_cookie
@cache_control(private=True)
@require_publisher
def update_podcast(request, podcast):

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    update_podcasts.delay([podcast.url])
    messages.success(
        request,
        _(
            "The update has been scheduled. It might take some time until the results are visible."
        ),
    )

    url = get_podcast_link_target(podcast, "podcast-publisher-detail")
    return HttpResponseRedirect(url)


@vary_on_cookie
@cache_control(private=True)
@require_publisher
def save_podcast(request, podcast):
    twitter = normalize_twitter(request.POST.get("twitter", ""))
    podcast.twitter = twitter
    podcast.save()
    messages.success(request, _("Data updated"))
    url = get_podcast_link_target(podcast, "podcast-publisher-detail")
    return HttpResponseRedirect(url)


@never_cache
@require_publisher
def new_update_token(request, username):
    request.user.profile.create_new_token("publisher_update_token")
    request.user.profile.save()
    messages.success(request, _("Publisher token updated"))
    return HttpResponseRedirect(reverse("publisher"))


@never_cache
@requires_token(token_name="publisher_update_token")
def update_published_podcasts(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    published_podcasts = [pp.podcast for pp in user.publishedpodcast_set.all()]
    update_podcasts.delay([podcast.url for podcast in published_podcasts])
    return HttpResponse(
        "Updated:\n" + "\n".join([p.url for p in published_podcasts]),
        content_type="text/plain",
    )


@vary_on_cookie
@cache_control(private=True)
@require_publisher
def episodes(request, podcast):

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    episodes = (
        Episode.objects.filter(podcast=podcast)
        .select_related("podcast")
        .prefetch_related("slugs", "podcast__slugs")
    )

    listeners = filter(None, (e.listeners for e in episodes))
    max_listeners = max(listeners, default=0)

    return render(
        request,
        "publisher/episodes.html",
        {"podcast": podcast, "episodes": episodes, "max_listeners": max_listeners},
    )


@require_publisher
@vary_on_cookie
@cache_control(private=True)
@allowed_methods(["GET", "POST"])
def episode(request, episode):

    site = RequestSite(request)
    podcast = episode.podcast

    if not check_publisher_permission(request.user, podcast):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = None  # EpisodeForm(request.POST, instance=e)
        # if form.is_valid():
        #    form.save()

    elif request.method == "GET":
        form = None  # EpisodeForm(instance=e)

    timeline_data = list(episode_listener_data(episode))

    return render(
        request,
        "publisher/episode.html",
        {
            "is_secure": request.is_secure(),
            "domain": site.domain,
            "episode": episode,
            "podcast": podcast,
            "form": form,
            "timeline_data": timeline_data,
        },
    )


@require_publisher
@never_cache
@allowed_methods(["POST"])
def update_episode_slug(request, episode):
    """ sets a new "main" slug, and moves the existing to the merged slugs """

    new_slug = request.POST.get("slug")
    podcast = episode.podcast

    if new_slug:
        # remove the new slug from other episodes (of the same podcast)
        other_episodes = Episode.objects.filter(
            podcast=podcast,
            slugs__slug=new_slug,
            slugs__content_type=ContentType.objects.get_for_model(Episode),
        )

        for other_episode in other_episodes:

            if other_episode == episode:
                continue

            other_episode.remove_slug(new_slug)
            messages.warning(
                request,
                _(
                    "Removed slug {slug} from {episode}".format(
                        slug=new_slug, episode=other_episode.title
                    )
                ),
            )

    episode.set_slug(new_slug)

    # TODO: we should use better cache invalidation
    cache.clear()

    return HttpResponseRedirect(
        get_episode_link_target(episode, podcast, "episode-publisher-detail")
    )


@vary_on_cookie
@cache_control(private=True)
def link(request):
    current_site = RequestSite(request)
    return render(request, "link.html", {"url": current_site})


@vary_on_cookie
@cache_control(private=True)
def advertise(request):
    site = RequestSite(request)
    return render(request, "publisher/advertise.html", {"site": site})


def group_id_decorator(f):
    @wraps(f)
    def _decorator(request, pg_slug, *args, **kwargs):
        group = get_object_or_404(PodcastGroup, pk=slug_id)
        return f(request, group, *args, **kwargs)

    return _decorator


episode_slug = episode_slug_decorator(episode)
update_episode_slug_slug = episode_slug_decorator(update_episode_slug)
podcast_slug = podcast_slug_decorator(podcast)
episodes_slug = podcast_slug_decorator(episodes)
update_podcast_slug = podcast_slug_decorator(update_podcast)
save_podcast_slug = podcast_slug_decorator(save_podcast)

episode_id = episode_id_decorator(episode)
update_episode_slug_id = episode_id_decorator(update_episode_slug)
podcast_id = podcast_id_decorator(podcast)
episodes_id = podcast_id_decorator(episodes)
update_podcast_id = podcast_id_decorator(update_podcast)
save_podcast_id = podcast_id_decorator(save_podcast)

group_slug = group_id_decorator(group)
group_id = group_id_decorator(group)
