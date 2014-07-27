import collections
from operator import itemgetter

from mygpo.utils import linearize
from mygpo.podcasts.models import Podcast
from mygpo.db.couchdb.user import get_num_listened_episodes


class PodcastSorter(object):
    """ Sorts a list of podcast """

    def __init__(self, podcasts):
        self.podcasts = podcasts
        self.sorted_podcasts = None


    def _sort(self):
        return self.podcasts


    def __len__(self):
        return len(self.podcasts)


    def __getitem__(self, val):
        if self.sorted_podcasts is None:
            self.sorted_podcasts = self._sort()

        return self.sorted_podcasts.__getitem__(val)

    def __iter__(self):
        if self.sorted_podcasts is None:
            self.sorted_podcasts = self._sort()

        return iter(self.sorted_podcasts)



class PodcastPercentageListenedSorter(PodcastSorter):
    """ Sorts podcasts by the percentage of listened episodes

    Adds the attributes percent_listened and episodes_listened to the podcasts

    Cost: 1 DB query """

    def __init__(self, podcasts, user):
        super(PodcastPercentageListenedSorter, self).__init__(podcasts)
        self.user = user


    def _sort(self):

        SORT_KEY = lambda podcast: podcast.percent_listened

        counts = dict(get_num_listened_episodes(self.user))
        for podcast in self.podcasts:
            c = counts.get(podcast.get_id(), 0)
            if podcast.episode_count:
                podcast.percent_listened = c / float(podcast.episode_count)
                podcast.episodes_listened = c
            else:
                podcast.percent_listened = 0
                podcast.episodes_listened = 0

        return sorted(self.podcasts, key=SORT_KEY, reverse=True)


def subscription_changes(device_id, podcast_states, since, until):
    """ returns subscription changes for the device and podcast states """

    add, rem = [], []
    for p_state in podcast_states:
        change = p_state.get_change_between(device_id, since, until)
        if change == 'subscribe':
            add.append( p_state.ref_url )
        elif change == 'unsubscribe':
            rem.append( p_state.ref_url )

    return add, rem


def podcasts_for_states(podcast_states):
    """ returns the podcasts corresponding to the podcast states """

    podcast_ids = [state.podcast for state in podcast_states]
    podcasts = Podcast.objects.filter(id__in=podcast_ids)
    podcasts = {podcast.id.hex: podcast for podcast in podcasts}
    return podcasts.values()



def get_subscribed_podcasts(user, public=None):
    """ Returns all subscribed podcasts for the user

    The attribute "url" contains the URL that was used when subscribing to
    the podcast """

    from mygpo.db.couchdb.podcast_state import get_subscribed_podcast_states_by_user
    states = get_subscribed_podcast_states_by_user(user.profile.uuid.hex, public)
    podcast_ids = [state.podcast for state in states]
    podcasts = Podcast.objects.filter(id__in=podcast_ids)
    podcasts = {podcast.id: podcast for podcast in podcasts}

    for state in states:
        podcast = podcasts.get(state.podcast, None)
        if podcast is None:
            continue

        podcast = proxy_object(podcast, url=state.ref_url)
        podcasts[state.podcast] = podcast

    return set(podcasts.values())


def get_subscriptions_by_device(user, public=None):
    from mygpo.db.couchdb.podcast_state import subscriptions_by_user
    get_dev = itemgetter(2)
    groups = collections.defaultdict(list)
    subscriptions = subscriptions_by_user(user, public=public)
    subscriptions = sorted(subscriptions, key=get_dev)

    for public, podcast_id, device_id in subscriptions:
        groups[device_id].append(podcast_id)

    return groups


def get_subscribed_podcast_ids(user, public=None):
    from mygpo.db.couchdb.podcast_state import get_subscribed_podcast_states_by_user
    states = get_subscribed_podcast_states_by_user(user, public)
    return [state.podcast for state in states]


def get_subscription_history(user, device_id=None, reverse=False, public=None):
    """ Returns chronologically ordered subscription history entries

    Setting device_id restricts the actions to a certain device
    """

    from mygpo.db.couchdb.podcast_state import podcast_states_for_user, \
        podcast_states_for_device
    from mygpo.users.models import HistoryEntry

    def action_iter(state):
        for action in sorted(state.actions, reverse=reverse):
            if device_id is not None and device_id != action.device:
                continue

            if public is not None and state.is_public() != public:
                continue

            entry = HistoryEntry()
            entry.timestamp = action.timestamp
            entry.action = action.action
            entry.podcast_id = state.podcast
            entry.device_id = action.device
            yield entry

    if device_id is None:
        podcast_states = podcast_states_for_user(user)
    else:
        podcast_states = podcast_states_for_device(device_id)

    # create an action_iter for each PodcastUserState
    subscription_action_lists = [action_iter(x) for x in podcast_states]

    action_cmp_key = lambda x: x.timestamp

    # Linearize their subscription-actions
    return linearize(action_cmp_key, subscription_action_lists, reverse)


def get_global_subscription_history(user, public=None):
    """ Actions that added/removed podcasts from the subscription list

    Returns an iterator of all subscription actions that either
     * added subscribed a podcast that hasn't been subscribed directly
       before the action (but could have been subscribed) earlier
     * removed a subscription of the podcast is not longer subscribed
       after the action
    """

    subscriptions = collections.defaultdict(int)

    for entry in get_subscription_history(user, public=public):
        if entry.action == 'subscribe':
            subscriptions[entry.podcast_id] += 1

            # a new subscription has been added
            if subscriptions[entry.podcast_id] == 1:
                yield entry

        elif entry.action == 'unsubscribe':
            subscriptions[entry.podcast_id] -= 1

            # the last subscription has been removed
            if subscriptions[entry.podcast_id] == 0:
                yield entry
