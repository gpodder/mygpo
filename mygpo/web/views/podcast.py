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

from mygpo.core.models import PodcastGroup, SubscriptionException
from mygpo.core.proxy import proxy_object
from mygpo.core.tasks import flattr_thing
from mygpo.utils import normalize_feed_url
from mygpo.users.settings import PUBLIC_SUB_PODCAST, FLATTR_TOKEN
from mygpo.publisher.utils import check_publisher_permission
from mygpo.users.models import HistoryEntry, DeviceDoesNotExist, SubscriptionAction
from mygpo.web.forms import SyncForm
from mygpo.decorators import allowed_methods, repeat_on_conflict
from mygpo.web.utils import get_podcast_link_target, get_page_list
from mygpo.db.couchdb.episode import episodes_for_podcast
from mygpo.db.couchdb.podcast import podcast_for_slug, podcast_for_slug_id, \
         podcast_for_oldid, podcast_for_url
from mygpo.db.couchdb.podcast_state import podcast_state_for_user_podcast, \
         add_subscription_action
from mygpo.db.couchdb.episode_state import get_podcasts_episode_states, \
         episode_listener_counts
from mygpo.db.couchdb.directory import tags_for_user, tags_for_podcast

import logging
logger = logging.getLogger(__name__)


MAX_TAGS_ON_PAGE=50


@repeat_on_conflict(['state'])
def update_podcast_settings(state, is_public):
    state.settings[PUBLIC_SUB_PODCAST.name] = is_public
    state.save()


@vary_on_cookie
@cache_control(private=True)
@allowed_methods(['GET'])
def show_slug(request, slug):
    podcast = podcast_for_slug(slug)

    if slug != podcast.slug:
        target = reverse('podcast_slug', args=[podcast.slug])
        return HttpResponseRedirect(target)

    return show(request, podcast.oldid)


@vary_on_cookie
@cache_control(private=True)
@allowed_methods(['GET'])
def show(request, podcast):
    """ Shows a podcast detail page """

    current_site = RequestSite(request)
    episodes = episode_list(podcast, request.user, limit=20)
    user = request.user

    max_listeners = max([e.listeners for e in episodes] + [0])

    episode = None

    if episodes:
        episode = episodes[0]
        episodes = episodes[1:]

    if podcast.group:
        group = PodcastGroup.get(podcast.group)
        rel_podcasts = filter(lambda x: x != podcast, group.podcasts)
    else:
        rel_podcasts = []

    tags = get_tags(podcast, user)

    if user.is_authenticated():
        state = podcast_state_for_user_podcast(user, podcast)
        subscribed_devices = state.get_subscribed_device_ids()
        subscribed_devices = [user.get_device(x) for x in subscribed_devices]

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

    return render(request, 'podcast.html', {
        'tags': tags,
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

    return tag_list


def episode_list(podcast, user, offset=0, limit=None):
    """
    Returns a list of episodes, with their action-attribute set to the latest
    action. The attribute is unsert if there is no episode-action for
    the episode.
    """

    listeners = dict(episode_listener_counts(podcast))
    episodes = episodes_for_podcast(podcast, descending=True, skip=offset, limit=limit)

    if user.is_authenticated():

        # prepare pre-populated data for HistoryEntry.fetch_data
        podcasts_dict = dict( (p_id, podcast) for p_id in podcast.get_ids())
        episodes_dict = dict( (episode._id, episode) for episode in episodes)

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

    episodes = episode_list(podcast, user, (page-1) * page_size,
            page_size)
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
    listener_count = listeners.pop(episode._id, None)
    action         = episode_actions.pop(episode._id, None)
    return proxy_object(episode, listeners=listener_count, action=action)



@never_cache
@login_required
def add_tag(request, podcast):
    podcast_state = podcast_state_for_user_podcast(request.user, podcast)

    tag_str = request.GET.get('tag', '')
    if not tag_str:
        return HttpResponseBadRequest()

    tags = tag_str.split(',')

    @repeat_on_conflict(['state'])
    def update(state):
        state.add_tags(tags)
        state.save()

    update(state=podcast_state)

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

    @repeat_on_conflict(['state'])
    def update(state):
        tags = list(state.tags)
        if tag_str in tags:
            state.tags.remove(tag_str)
            state.save()

    update(state=podcast_state)

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
            device_uids.append(request.POST.get('targets'))

        for uid in device_uids:
            try:
                device = request.user.get_device_by_uid(uid)
                podcast.subscribe(request.user, device)

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
        podcast.unsubscribe(request.user, device)
    except SubscriptionException as e:
        logger.exception('Web: %(username)s: could not unsubscribe from podcast %(podcast_url)s on device %(device_id)s' %
            {'username': request.user.username, 'podcast_url': podcast.url, 'device_id': device.id})

    return HttpResponseRedirect(return_to)


@never_cache
@login_required
def subscribe_url(request):
    url = request.GET.get('url', None)

    if not url:
        raise Http404('http://my.gpodder.org/subscribe?url=http://www.example.com/podcast.xml')

    url = normalize_feed_url(url)

    if not url:
        raise Http404('Please specify a valid url')

    podcast = podcast_for_url(url, create=True)

    return HttpResponseRedirect(get_podcast_link_target(podcast, 'subscribe'))


@never_cache
@allowed_methods(['POST'])
def set_public(request, podcast, public):
    state = podcast_state_for_user_podcast(request.user, podcast)
    update_podcast_settings(state=state, is_public=public)
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


# To make all view accessible via either CouchDB-ID or Slugs
# a decorator queries the podcast and passes the Id on to the
# regular views

def slug_id_decorator(f):
    @wraps(f)
    def _decorator(request, slug_id, *args, **kwargs):
        podcast = podcast_for_slug_id(slug_id)

        if podcast is None:
            raise Http404

        # redirect when Id or a merged (non-cannonical) slug is used
        if podcast.slug and slug_id != podcast.slug:
            return HttpResponseRedirect(get_podcast_link_target(podcast))

        return f(request, podcast, *args, **kwargs)

    return _decorator


def oldid_decorator(f):
    @wraps(f)
    def _decorator(request, pid, *args, **kwargs):
        try:
            pid = int(pid)
        except (TypeError, ValueError):
            raise Http404

        podcast = podcast_for_oldid(pid)

        if not podcast:
            raise Http404

        # redirect to Id or slug URL
        return HttpResponseRedirect(get_podcast_link_target(podcast))

    return _decorator


show_slug_id        = slug_id_decorator(show)
subscribe_slug_id   = slug_id_decorator(subscribe)
unsubscribe_slug_id = slug_id_decorator(unsubscribe)
add_tag_slug_id     = slug_id_decorator(add_tag)
remove_tag_slug_id  = slug_id_decorator(remove_tag)
set_public_slug_id  = slug_id_decorator(set_public)
all_episodes_slug_id= slug_id_decorator(all_episodes)
flattr_podcast_slug_id=slug_id_decorator(flattr_podcast)
history_podcast_slug_id= slug_id_decorator(history)


show_oldid          = oldid_decorator(show)
subscribe_oldid     = oldid_decorator(subscribe)
unsubscribe_oldid   = oldid_decorator(unsubscribe)
add_tag_oldid       = oldid_decorator(add_tag)
remove_tag_oldid    = oldid_decorator(remove_tag)
set_public_oldid    = oldid_decorator(set_public)
all_episodes_oldid  = oldid_decorator(all_episodes)
flattr_podcast_oldid= oldid_decorator(flattr_podcast)
history_podcast_oldid= oldid_decorator(history)
