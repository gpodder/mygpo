from functools import wraps, partial

from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import RequestSite
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache, cache_control
from django.shortcuts import get_object_or_404

from mygpo.podcasts.models import Podcast, PodcastGroup, Episode
from mygpo.users.models import SubscriptionException
from mygpo.core.proxy import proxy_object
from mygpo.core.tasks import flattr_thing
from mygpo.utils import normalize_feed_url
from mygpo.users.settings import PUBLIC_SUB_PODCAST, FLATTR_TOKEN
from mygpo.publisher.utils import check_publisher_permission
from mygpo.users.models import HistoryEntry, DeviceDoesNotExist, SubscriptionAction
from mygpo.web.forms import SyncForm
from mygpo.decorators import allowed_methods, repeat_on_conflict
from mygpo.web.utils import get_podcast_link_target, get_page_list, \
    check_restrictions
from mygpo.db.couchdb.podcast_state import podcast_state_for_user_podcast, \
         add_subscription_action, add_podcast_tags, remove_podcast_tags, \
         set_podcast_privacy_settings, subscribe as subscribe_podcast, \
         unsubscribe as unsubscribe_podcast
from mygpo.db.couchdb.episode_state import get_podcasts_episode_states, \
         episode_listener_counts
from mygpo.db.couchdb.directory import tags_for_user, tags_for_podcast

import logging
logger = logging.getLogger(__name__)


MAX_TAGS_ON_PAGE=50


@vary_on_cookie
@cache_control(private=True)
@allowed_methods(['GET'])
def show(request, podcast):
    """ Shows a podcast detail page """

    podcast = check_restrictions(podcast)

    current_site = RequestSite(request)
    num_episodes = 20
    episodes = episode_list(podcast, request.user, limit=num_episodes)
    user = request.user

    max_listeners = max([e.listeners for e in episodes] + [0])

    episode = None

    if episodes:
        episode = episodes[0]
        episodes = episodes[1:]

    if podcast.group:
        group = podcast.group
        rel_podcasts = group.podcast_set.exclude(pk=podcast.pk)
    else:
        rel_podcasts = []

    tags, has_tagged = get_tags(podcast, user)

    if user.is_authenticated():
        state = podcast_state_for_user_podcast(user, podcast)
        subscribed_devices = state.get_subscribed_device_ids()
        subscribed_devices = user.get_devices(subscribed_devices)

        subscribe_targets = podcast.subscribe_targets(user)

        has_history = bool(state.actions)
        is_public = state.settings.get('public_subscription', True)
        can_flattr = request.user.get_wksetting(FLATTR_TOKEN) and podcast.flattr_url

    else:
        has_history = False
        is_public = False
        subscribed_devices = []
        subscribe_targets = []
        can_flattr = False

    is_publisher = check_publisher_permission(user, podcast)

    episodes_total = podcast.episode_count or 0
    num_pages = episodes_total / num_episodes
    page_list = get_page_list(1, num_pages, 1, 15)

    return render(request, 'podcast.html', {
        'tags': tags,
        'has_tagged': has_tagged,
        'url': current_site,
        'has_history': has_history,
        'podcast': podcast,
        'is_public': is_public,
        'devices': subscribed_devices,
        'related_podcasts': rel_podcasts,
        'can_subscribe': len(subscribe_targets) > 0,
        'subscribe_targets': subscribe_targets,
        'episode': episode,
        'episodes': episodes,
        'max_listeners': max_listeners,
        'can_flattr': can_flattr,
        'is_publisher': is_publisher,
        'page_list': page_list,
        'current_page': 1,
    })


def get_tags(podcast, user):
    tags = {}
    for t in tags_for_podcast(podcast):
        tag_str = t.lower()
        tags[tag_str] = False

    if not user.is_anonymous():
        users_tags = tags_for_user(user, podcast.get_id())
        for t in users_tags.get(podcast.get_id(), []):
            tag_str = t.lower()
            tags[tag_str] = True

    tag_list = [{'tag': key, 'is_own': value} for key, value in tags.iteritems()]
    tag_list.sort(key=lambda x: x['tag'])

    if len(tag_list) > MAX_TAGS_ON_PAGE:
        tag_list = filter(lambda x: x['is_own'], tag_list)
        tag_list.append({'tag': '...', 'is_own': False})

    has_own = any(t['is_own'] for t in tag_list)

    return tag_list, has_own


def episode_list(podcast, user, offset=0, limit=None):
    """
    Returns a list of episodes, with their action-attribute set to the latest
    action. The attribute is unsert if there is no episode-action for
    the episode.
    """

    listeners = dict(episode_listener_counts(podcast))
    episodes = Episode.objects.filter(podcast=podcast).all().by_released()
    episodes = list(episodes.prefetch_related('slugs')[offset:offset+limit])

    if user.is_authenticated():

        # prepare pre-populated data for HistoryEntry.fetch_data
        podcasts_dict = {podcast.get_id(): podcast}
        episodes_dict = dict( (episode.id, episode) for episode in episodes)

        actions = get_podcasts_episode_states(podcast, user._id)
        actions = map(HistoryEntry.from_action_dict, actions)

        HistoryEntry.fetch_data(user, actions,
                podcasts=podcasts_dict, episodes=episodes_dict)

        episode_actions = dict( (action.episode_id, action) for action in actions)
    else:
        episode_actions = {}

    annotate_episode = partial(_annotate_episode, listeners, episode_actions)
    return map(annotate_episode, episodes)



@never_cache
@login_required
def history(request, podcast):
    """ shows the subscription history of the user """

    user = request.user
    state = podcast_state_for_user_podcast(user, podcast)
    history = list(state.actions)

    def _set_objects(h):
        dev = user.get_device(h.device)
        return proxy_object(h, device=dev)
    history = map(_set_objects, history)

    return render(request, 'podcast-history.html', {
        'history': history,
        'podcast': podcast,
    })


def all_episodes(request, podcast, page_size=20):

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    user = request.user

    episodes = episode_list(podcast, user, (page-1) * page_size, page_size)
    episodes_total = podcast.episode_count or 0
    num_pages = episodes_total / page_size
    page_list = get_page_list(1, num_pages, page, 15)

    max_listeners = max([e.listeners for e in episodes] + [0])

    is_publisher = check_publisher_permission(user, podcast)

    return render(request, 'episodes.html', {
        'podcast': podcast,
        'episodes': episodes,
        'max_listeners': max_listeners,
        'page_list': page_list,
        'current_page': page,
        'is_publisher': is_publisher,
    })



def _annotate_episode(listeners, episode_actions, episode):
    episode.listener_count = listeners.pop(episode.get_id(), None)
    episode.action = episode_actions.pop(episode.get_id(), None)
    return episode



@never_cache
@login_required
def add_tag(request, podcast):
    podcast_state = podcast_state_for_user_podcast(request.user, podcast)

    tag_str = request.GET.get('tag', '')
    if not tag_str:
        return HttpResponseBadRequest()

    tags = tag_str.split(',')
    add_podcast_tags(podcast_state, tags)

    if request.GET.get('next', '') == 'mytags':
        return HttpResponseRedirect('/tags/')

    return HttpResponseRedirect(get_podcast_link_target(podcast))


@never_cache
@login_required
def remove_tag(request, podcast):
    podcast_state = podcast_state_for_user_podcast(request.user, podcast)

    tag_str = request.GET.get('tag', '')
    if not tag_str:
        return HttpResponseBadRequest()

    remove_podcast_tags(podcast_state, tag_str)

    if request.GET.get('next', '') == 'mytags':
        return HttpResponseRedirect('/tags/')

    return HttpResponseRedirect(get_podcast_link_target(podcast))


@never_cache
@login_required
@allowed_methods(['GET', 'POST'])
def subscribe(request, podcast):

    if request.method == 'POST':

        # multiple UIDs from the /podcast/<slug>/subscribe
        device_uids = [k for (k,v) in request.POST.items() if k==v]

        # single UID from /podcast/<slug>
        if 'targets' in request.POST:
            devices = request.POST.get('targets')
            devices = devices.split(',')
            device_uids.extend(devices)

        for uid in device_uids:
            try:
                device = request.user.get_device_by_uid(uid)
                subscribe_podcast(podcast, request.user, device)

            except (SubscriptionException, DeviceDoesNotExist, ValueError) as e:
                messages.error(request, str(e))

        return HttpResponseRedirect(get_podcast_link_target(podcast))

    targets = podcast.subscribe_targets(request.user)

    return render(request, 'subscribe.html', {
        'targets': targets,
        'podcast': podcast,
    })


@never_cache
@login_required
@allowed_methods(['POST'])
def subscribe_all(request, podcast):
    """ subscribe all of the user's devices to the podcast """
    user = request.user

    devs = podcast.subscribe_targets(user)
    # ungroup groups
    devs = [dev[0] if isinstance(dev, list) else dev for dev in devs]

    try:
        subscribe_podcast(podcast, user, devs)
    except (SubscriptionException, DeviceDoesNotExist, ValueError) as e:
        messages.error(request, str(e))

    return HttpResponseRedirect(get_podcast_link_target(podcast))


@never_cache
@login_required
def unsubscribe(request, podcast, device_uid):

    return_to = request.GET.get('return_to', None)

    if not return_to:
        raise Http404('Wrong URL')

    try:
        device = request.user.get_device_by_uid(device_uid)

    except DeviceDoesNotExist as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(return_to)

    try:
        unsubscribe_podcast(podcast, request.user, device)
    except SubscriptionException as e:
        logger.exception('Web: %(username)s: could not unsubscribe from podcast %(podcast_url)s on device %(device_id)s' %
            {'username': request.user.username, 'podcast_url': podcast.url, 'device_id': device.id})

    return HttpResponseRedirect(return_to)


@never_cache
@login_required
@allowed_methods(['POST'])
def unsubscribe_all(request, podcast):
    """ unsubscribe all of the user's devices from the podcast """

    user = request.user
    state = podcast_state_for_user_podcast(user, podcast)

    dev_ids = state.get_subscribed_device_ids()
    devs = user.get_devices(dev_ids)
    # ungroup groups
    devs = [dev[0] if isinstance(dev, list) else dev for dev in devs]

    try:
        unsubscribe_podcast(podcast, user, devs)
    except (SubscriptionException, DeviceDoesNotExist, ValueError) as e:
        messages.error(request, str(e))

    return HttpResponseRedirect(get_podcast_link_target(podcast))


@never_cache
@login_required
def subscribe_url(request):
    url = request.GET.get('url', None)

    if not url:
        raise Http404('http://my.gpodder.org/subscribe?url=http://www.example.com/podcast.xml')

    url = normalize_feed_url(url)

    if not url:
        raise Http404('Please specify a valid url')

    podcast = Podcasts.objects.get_or_create_for_url(url)

    return HttpResponseRedirect(get_podcast_link_target(podcast, 'subscribe'))


@never_cache
@allowed_methods(['POST'])
def set_public(request, podcast, public):
    state = podcast_state_for_user_podcast(request.user, podcast)
    set_podcast_privacy_settings(state, public)
    return HttpResponseRedirect(get_podcast_link_target(podcast))


@never_cache
@login_required
def flattr_podcast(request, podcast):
    """ Flattrs a podcast, records an event and redirects to the podcast """

    user = request.user
    site = RequestSite(request)

    # do flattring via the tasks queue, but wait for the result
    task = flattr_thing.delay(user, podcast.get_id(), site.domain,
            request.is_secure(), 'Podcast')
    success, msg = task.get()

    if success:
        action = SubscriptionAction()
        action.action = 'flattr'
        state = podcast_state_for_user_podcast(request.user, podcast)
        add_subscription_action(state, action)
        messages.success(request, _("Flattr\'d"))

    else:
        messages.error(request, msg)

    return HttpResponseRedirect(get_podcast_link_target(podcast))


# To make all view accessible via either IDs or Slugs
# a decorator queries the podcast and passes the Id on to the
# regular views

def slug_decorator(f):
    @wraps(f)
    def _decorator(request, slug, *args, **kwargs):

        try:
            podcast = Podcast.objects.filter(slugs__slug=slug)
            podcast = podcast.prefetch_related('slugs', 'urls').get()
        except Podcast.DoesNotExist:
            raise Http404

        # redirect when a non-cannonical slug is used
        if slug != podcast.slug:
            return HttpResponseRedirect(get_podcast_link_target(podcast))

        return f(request, podcast, *args, **kwargs)

    return _decorator


def id_decorator(f):
    @wraps(f)
    def _decorator(request, podcast_id, *args, **kwargs):

        try:
            podcast = Podcast.objects.filter(id=podcast_id)
            podcast = podcast.prefetch_related('slugs', 'urls').get()

            # if the podcast has a slug, redirect to its canonical URL
            if podcast.slug:
                return HttpResponseRedirect(get_podcast_link_target(podcast))

            return f(request, podcast, *args, **kwargs)

        except Podcast.DoesNotExist:
            podcast = get_object_or_404(Podcast, merged_uuids__uuid=podcast_id)
            return HttpResponseRedirect(get_podcast_link_target(podcast))

    return _decorator


show_slug            = slug_decorator(show)
subscribe_slug       = slug_decorator(subscribe)
subscribe_all_slug   = slug_decorator(subscribe_all)
unsubscribe_slug     = slug_decorator(unsubscribe)
unsubscribe_all_slug = slug_decorator(unsubscribe_all)
add_tag_slug         = slug_decorator(add_tag)
remove_tag_slug      = slug_decorator(remove_tag)
set_public_slug      = slug_decorator(set_public)
all_episodes_slug    = slug_decorator(all_episodes)
flattr_podcast_slug  = slug_decorator(flattr_podcast)
history_podcast_slug = slug_decorator(history)


show_id            = id_decorator(show)
subscribe_id       = id_decorator(subscribe)
subscribe_all_id   = id_decorator(subscribe_all)
unsubscribe_id     = id_decorator(unsubscribe)
unsubscribe_all_id = id_decorator(unsubscribe_all)
add_tag_id         = id_decorator(add_tag)
remove_tag_id      = id_decorator(remove_tag)
set_public_id      = id_decorator(set_public)
all_episodes_id    = id_decorator(all_episodes)
flattr_podcast_id  = id_decorator(flattr_podcast)
history_podcast_id = id_decorator(history)
