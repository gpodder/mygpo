from collections import defaultdict

from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib.sites.requests import RequestSite
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control

from mygpo.podcasts.models import Podcast, Tag
from mygpo.subscriptions import get_subscribed_podcasts
from mygpo.web.utils import process_lang_params
from mygpo.podcastlists.models import PodcastList
from mygpo.favorites.models import FavoriteEpisode

# from mygpo.web.views.podcast import slug_id_decorator
from mygpo.publisher.models import PublishedPodcast


@vary_on_cookie
@cache_control(private=True)
def home(request):
    if request.user.is_authenticated:
        return dashboard(request)
    else:
        return welcome(request)


@vary_on_cookie
@cache_control(private=True)
def welcome(request):
    current_site = RequestSite(request)

    lang = process_lang_params(request)

    toplist = Podcast.objects.all().toplist(lang)

    return render(request, "home.html", {"url": current_site, "toplist": toplist})


@vary_on_cookie
@cache_control(private=True)
@login_required
def dashboard(request, episode_count=10):

    subscribed_podcasts = get_subscribed_podcasts(request.user)
    subscribed_podcasts = [sp.podcast for sp in subscribed_podcasts]

    podcast_ad = Podcast.objects.get_advertised_podcast()

    site = RequestSite(request)

    checklist = []

    if request.user.client_set.count():
        checklist.append("devices")

    if subscribed_podcasts:
        checklist.append("subscriptions")

    if FavoriteEpisode.objects.filter(user=request.user).exists():
        checklist.append("favorites")

    if not request.user.profile.get_token("subscriptions_token"):
        checklist.append("share")

    if not request.user.profile.get_token("favorite_feeds_token"):
        checklist.append("share-favorites")

    if not request.user.profile.get_token("userpage_token"):
        checklist.append("userpage")

    if Tag.objects.filter(user=request.user).exists():
        checklist.append("tags")

    if PodcastList.objects.filter(user=request.user).exists():
        checklist.append("lists")

    if PublishedPodcast.objects.filter(publisher=request.user).exists():
        checklist.append("publish")

    newest_episodes = []

    # we only show the "install reader" link in firefox, because we don't know
    # yet how/if this works in other browsers.
    # hints appreciated at https://bugs.gpodder.org/show_bug.cgi?id=58
    show_install_reader = "firefox" in request.META.get("HTTP_USER_AGENT", "").lower()

    random_podcast = Podcast.objects.all().random().prefetch_related("slugs").first()

    return render(
        request,
        "dashboard.html",
        {
            "user": request.user,
            "subscribed_podcasts": subscribed_podcasts,
            "newest_episodes": list(newest_episodes),
            "random_podcast": random_podcast,
            "checklist": checklist,
            "site": site,
            "show_install_reader": show_install_reader,
            "podcast_ad": podcast_ad,
        },
    )


@vary_on_cookie
@cache_control(private=True)
@login_required
def mytags(request):
    tags_tag = defaultdict(list)

    user = request.user

    tags = Tag.objects.filter(source=Tag.USER, user=user).order_by("tag")
    for tag in tags:
        tags_tag[tag.tag].append(tag.content_object)

    return render(request, "mytags.html", {"tags_tag": dict(tags_tag.items())})


@never_cache
def csrf_failure(request, reason=""):
    site = RequestSite(request)
    return render(
        request,
        "csrf.html",
        {
            "site": site,
            "method": request.method,
            "referer": request.META.get("HTTP_REFERER", _("another site")),
            "path": request.path,
            "get": request.GET,
            "post": request.POST,
        },
    )
