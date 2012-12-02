import re
import uuid, collections
from datetime import datetime
import dateutil.parser
from itertools import imap
from operator import itemgetter
import random
import string

from couchdbkit.ext.django.schema import *

from django.core.cache import cache

from django_couchdb_utils.registration.models import User as BaseUser

from mygpo.core.models import Podcast
from mygpo.utils import linearize
from mygpo.core.proxy import DocumentABCMeta, proxy_object
from mygpo.decorators import repeat_on_conflict
from mygpo.users.ratings import RatingMixin
from mygpo.users.sync import SyncedDevicesMixin
from mygpo.users.settings import FAV_FLAG, PUBLIC_SUB_PODCAST, SettingsMixin
from mygpo.db.couchdb.podcast import podcasts_by_id, podcasts_to_dict
from mygpo.db.couchdb.user import user_history, device_history


RE_DEVICE_UID = re.compile(r'^[\w.-]+$')


class InvalidEpisodeActionAttributes(ValueError):
    """ raised when the attribues of an episode action fail validation """


class DeviceUIDException(Exception):
    pass


class DeviceDoesNotExist(Exception):
    pass


class DeviceDeletedException(DeviceDoesNotExist):
    pass


class Suggestions(Document, RatingMixin):
    user = StringProperty(required=True)
    user_oldid = IntegerProperty()
    podcasts = StringListProperty()
    blacklist = StringListProperty()


    def get_podcasts(self, count=None):
        user = User.get(self.user)
        subscriptions = user.get_subscribed_podcast_ids()

        ids = filter(lambda x: not x in self.blacklist + subscriptions, self.podcasts)
        if count:
            ids = ids[:count]
        return filter(lambda x: x and x.title, podcasts_by_id(ids))


    def __repr__(self):
        if not self._id:
            return super(Suggestions, self).__repr__()
        else:
            return '%d Suggestions for %s (%s)' % \
                (len(self.podcasts), self.user, self._id)


class EpisodeAction(DocumentSchema):
    """
    One specific action to an episode. Must
    always be part of a EpisodeUserState
    """

    action        = StringProperty(required=True)
    timestamp     = DateTimeProperty(required=True, default=datetime.utcnow)
    device_oldid  = IntegerProperty(required=False)
    device        = StringProperty()
    started       = IntegerProperty()
    playmark      = IntegerProperty()
    total         = IntegerProperty()

    def __eq__(self, other):
        if not isinstance(other, EpisodeAction):
            return False
        vals = ('action', 'timestamp', 'device', 'started', 'playmark',
                'total')
        return all([getattr(self, v, None) == getattr(other, v, None) for v in vals])


    def to_history_entry(self):
        entry = HistoryEntry()
        entry.action = self.action
        entry.timestamp = self.timestamp
        entry.device_id = self.device
        entry.started = self.started
        entry.position = self.playmark
        entry.total = self.total
        return entry



    def validate_time_values(self):
        """ Validates allowed combinations of time-values """

        PLAY_ACTION_KEYS = ('playmark', 'started', 'total')

        # Key found, but must not be supplied (no play action!)
        if self.action != 'play':
            for key in PLAY_ACTION_KEYS:
                if getattr(self, key, None) is not None:
                    raise InvalidEpisodeActionAttributes('%s only allowed in play actions' % key)

        # Sanity check: If started or total are given, require playmark
        if ((self.started is not None) or (self.total is not None)) and \
            self.playmark is None:
            raise InvalidEpisodeActionAttributes('started and total require position')

        # Sanity check: total and playmark can only appear together
        if ((self.total is not None) or (self.started is not None)) and \
           ((self.total is None)     or (self.started is None)):
            raise InvalidEpisodeActionAttributes('total and started can only appear together')


    def __repr__(self):
        return '%s-Action on %s at %s (in %s)' % \
            (self.action, self.device, self.timestamp, self._id)


    def __hash__(self):
        return hash(frozenset([self.action, self.timestamp, self.device,
                    self.started, self.playmark, self.total]))


class Chapter(Document):
    """ A user-entered episode chapter """

    device = StringProperty()
    created = DateTimeProperty()
    start = IntegerProperty(required=True)
    end = IntegerProperty(required=True)
    label = StringProperty()
    advertisement = BooleanProperty()


    def __repr__(self):
        return '<%s %s (%d-%d)>' % (self.__class__.__name__, self.label,
                self.start, self.end)


class EpisodeUserState(Document, SettingsMixin):
    """
    Contains everything a user has done with an Episode
    """

    episode       = StringProperty(required=True)
    actions       = SchemaListProperty(EpisodeAction)
    user_oldid    = IntegerProperty()
    user          = StringProperty(required=True)
    ref_url       = StringProperty(required=True)
    podcast_ref_url = StringProperty(required=True)
    merged_ids    = StringListProperty()
    chapters      = SchemaListProperty(Chapter)
    podcast       = StringProperty(required=True)
    # TODO: add a StringListProperty containing the timestamps of all
    # successful flattrs



    def add_actions(self, actions):
        map(EpisodeAction.validate_time_values, actions)

        # TODO: trigger flattring if action contains a play-event
        # TODO: add current time to list of flattr-timestamps if flattring
        # was successful

        self.actions = list(self.actions) + actions
        self.actions = list(set(self.actions))
        self.actions = sorted(self.actions, key=lambda x: x.timestamp)


    def is_favorite(self):
        return self.get_wksetting(FAV_FLAG)


    def set_favorite(self, set_to=True):
        self.settings[FAV_FLAG.name] = set_to


    def update_chapters(self, add=[], rem=[]):
        """ Updates the Chapter list

         * add contains the chapters to be added

         * rem contains tuples of (start, end) times. Chapters that match
           both endpoints will be removed
        """

        @repeat_on_conflict(['state'])
        def update(state):
            for chapter in add:
                self.chapters = self.chapters + [chapter]

            for start, end in rem:
                keep = lambda c: c.start != start or c.end != end
                self.chapters = filter(keep, self.chapters)

            self.save()

        update(state=self)


    def get_history_entries(self):
        return imap(EpisodeAction.to_history_entry, self.actions)


    def __repr__(self):
        return 'Episode-State %s (in %s)' % \
            (self.episode, self._id)

    def __eq__(self, other):
        if not isinstance(other, EpisodeUserState):
            return False

        return (self.episode == other.episode and
                self.user == other.user)



class SubscriptionAction(Document):
    action    = StringProperty()
    timestamp = DateTimeProperty(default=datetime.utcnow)
    device    = StringProperty()


    __metaclass__ = DocumentABCMeta


    def __cmp__(self, other):
        return cmp(self.timestamp, other.timestamp)

    def __eq__(self, other):
        return self.action == other.action and \
               self.timestamp == other.timestamp and \
               self.device == other.device

    def __hash__(self):
        return hash(self.action) + hash(self.timestamp) + hash(self.device)

    def __repr__(self):
        return '<SubscriptionAction %s on %s at %s>' % (
            self.action, self.device, self.timestamp)


class PodcastUserState(Document, SettingsMixin):
    """
    Contains everything that a user has done
    with a specific podcast and all its episodes
    """

    podcast       = StringProperty(required=True)
    user_oldid    = IntegerProperty()
    user          = StringProperty(required=True)
    actions       = SchemaListProperty(SubscriptionAction)
    tags          = StringListProperty()
    ref_url       = StringProperty(required=True)
    disabled_devices = StringListProperty()
    merged_ids    = StringListProperty()

    # TODO: a flag for enabling auto-flattring per podcast can be stored
    # in the settings field; would be automatically accessible through
    # the Settings API


    def remove_device(self, device):
        """
        Removes all actions from the podcast state that refer to the
        given device
        """
        self.actions = filter(lambda a: a.device != device.id, self.actions)


    def subscribe(self, device):
        action = SubscriptionAction()
        action.action = 'subscribe'
        action.device = device.id
        self.add_actions([action])


    def unsubscribe(self, device):
        action = SubscriptionAction()
        action.action = 'unsubscribe'
        action.device = device.id
        self.add_actions([action])


    def add_actions(self, actions):
        self.actions = list(set(self.actions + actions))
        self.actions = sorted(self.actions)


    def add_tags(self, tags):
        self.tags = list(set(self.tags + tags))


    def set_device_state(self, devices):
        disabled_devices = [device.id for device in devices if device.deleted]
        self.disabled_devices = disabled_devices


    def get_change_between(self, device_id, since, until):
        """
        Returns the change of the subscription status for the given device
        between the two timestamps.

        The change is given as either 'subscribe' (the podcast has been
        subscribed), 'unsubscribed' (the podcast has been unsubscribed) or
        None (no change)
        """

        device_actions = filter(lambda x: x.device == device_id, self.actions)
        before = filter(lambda x: x.timestamp <= since, device_actions)
        after  = filter(lambda x: x.timestamp <= until, device_actions)

        # nothing happened, so there can be no change
        if not after:
            return None

        then = before[-1] if before else None
        now  = after[-1]

        if then is None:
            if now.action != 'unsubscribe':
                return now.action
        elif then.action != now.action:
            return now.action
        return None


    def get_subscribed_device_ids(self):
        """ device Ids on which the user subscribed to the podcast """
        devices = set()

        for action in self.actions:
            if action.action == "subscribe":
                if not action.device in self.disabled_devices:
                    devices.add(action.device)
            else:
                if action.device in devices:
                    devices.remove(action.device)

        return devices



    def is_public(self):
        return self.get_wksetting(PUBLIC_SUB_PODCAST)


    def __eq__(self, other):
        if other is None:
            return False

        return self.podcast == other.podcast and \
               self.user == other.user

    def __repr__(self):
        return 'Podcast %s for User %s (%s)' % \
            (self.podcast, self.user, self._id)


class Device(Document, SettingsMixin):
    id       = StringProperty(default=lambda: uuid.uuid4().hex)
    oldid    = IntegerProperty(required=False)
    uid      = StringProperty(required=True)
    name     = StringProperty(required=True, default='New Device')
    type     = StringProperty(required=True, default='other')
    deleted  = BooleanProperty(default=False)
    user_agent = StringProperty()


    def get_subscription_changes(self, since, until):
        """
        Returns the subscription changes for the device as two lists.
        The first lists contains the Ids of the podcasts that have been
        subscribed to, the second list of those that have been unsubscribed
        from.
        """

        from mygpo.db.couchdb.podcast_state import podcast_states_for_device

        add, rem = [], []
        podcast_states = podcast_states_for_device(self.id)
        for p_state in podcast_states:
            change = p_state.get_change_between(self.id, since, until)
            if change == 'subscribe':
                add.append( p_state.ref_url )
            elif change == 'unsubscribe':
                rem.append( p_state.ref_url )

        return add, rem


    def get_latest_changes(self):

        from mygpo.db.couchdb.podcast_state import podcast_states_for_device

        podcast_states = podcast_states_for_device(self.id)
        for p_state in podcast_states:
            actions = filter(lambda x: x.device == self.id, reversed(p_state.actions))
            if actions:
                yield (p_state.podcast, actions[0])


    def get_subscribed_podcast_states(self):
        r = PodcastUserState.view('subscriptions/by_device',
                startkey     = [self.id, None],
                endkey       = [self.id, {}],
                include_docs = True
            )
        return list(r)


    def get_subscribed_podcast_ids(self):
        states = self.get_subscribed_podcast_states()
        return [state.podcast for state in states]


    def get_subscribed_podcasts(self):
        """ Returns all subscribed podcasts for the device

        The attribute "url" contains the URL that was used when subscribing to
        the podcast """

        states = self.get_subscribed_podcast_states()
        podcast_ids = [state.podcast for state in states]
        podcasts = podcasts_to_dict(podcast_ids)

        for state in states:
            podcast = proxy_object(podcasts[state.podcast], url=state.ref_url)
            podcasts[state.podcast] = podcast

        return podcasts.values()


    def __hash__(self):
        return hash(frozenset([self.id, self.uid, self.name, self.type, self.deleted]))


    def __eq__(self, other):
        return self.id == other.id


    def __repr__(self):
        return '<{cls} {id}>'.format(cls=self.__class__.__name__, id=self.id)


    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name



TOKEN_NAMES = ('subscriptions_token', 'favorite_feeds_token',
        'publisher_update_token', 'userpage_token')


class TokenException(Exception):
    pass


class User(BaseUser, SyncedDevicesMixin, SettingsMixin):
    oldid    = IntegerProperty()
    devices  = SchemaListProperty(Device)
    published_objects = StringListProperty()
    deleted  = BooleanProperty(default=False)
    suggestions_up_to_date = BooleanProperty(default=False)
    twitter = StringProperty()
    about   = StringProperty()
    # TODO: add fields for storing flattr account info (token / enabled flag)

    # token for accessing subscriptions of this use
    subscriptions_token    = StringProperty(default=None)

    # token for accessing the favorite-episodes feed of this user
    favorite_feeds_token   = StringProperty(default=None)

    # token for automatically updating feeds published by this user
    publisher_update_token = StringProperty(default=None)

    # token for accessing the userpage of this user
    userpage_token         = StringProperty(default=None)

    class Meta:
        app_label = 'users'


    def create_new_token(self, token_name, length=32):
        """ creates a new random token """

        if token_name not in TOKEN_NAMES:
            raise TokenException('Invalid token name %s' % token_name)

        token = "".join(random.sample(string.letters+string.digits, length))
        setattr(self, token_name, token)



    def get_token(self, token_name):
        """ returns a token, and generate those that are still missing """

        generated = False

        if token_name not in TOKEN_NAMES:
            raise TokenException('Invalid token name %s' % token_name)

        for tn in TOKEN_NAMES:
            if getattr(self, tn) is None:
                self.create_new_token(tn)
                generated = True

        if generated:
            self.save()

        return getattr(self, token_name)



    @property
    def active_devices(self):
        not_deleted = lambda d: not d.deleted
        return filter(not_deleted, self.devices)


    @property
    def inactive_devices(self):
        deleted = lambda d: d.deleted
        return filter(deleted, self.devices)


    def get_devices_by_id(self):
        return dict( (device.id, device) for device in self.devices)


    def get_device(self, id):

        if not hasattr(self, '__device_by_id'):
            self.__devices_by_id = dict( (d.id, d) for d in self.devices)

        return self.__devices_by_id.get(id, None)


    def get_device_by_uid(self, uid, only_active=True):

        if not hasattr(self, '__devices_by_uio'):
            self.__devices_by_uid = dict( (d.uid, d) for d in self.devices)

        try:
            device = self.__devices_by_uid[uid]

            if only_active and device.deleted:
                raise DeviceDeletedException(
                        'Device with UID %s is deleted' % uid)

            return device

        except KeyError as e:
            raise DeviceDoesNotExist('There is no device with UID %s' % uid)


    def update_device(self, device):
        """ Sets the device and saves the user """

        @repeat_on_conflict(['user'])
        def _update(user, device):
            user.set_device(device)
            user.save()

        _update(user=self, device=device)


    def set_device(self, device):

        if not RE_DEVICE_UID.match(device.uid):
            raise DeviceUIDException(u"'{uid} is not a valid device ID".format(
                        uid=device.uid))

        devices = list(self.devices)
        ids = [x.id for x in devices]
        if not device.id in ids:
            devices.append(device)
            self.devices = devices
            return

        index = ids.index(device.id)
        devices.pop(index)
        devices.insert(index, device)
        self.devices = devices


    def remove_device(self, device):
        devices = list(self.devices)
        ids = [x.id for x in devices]
        if not device.id in ids:
            return

        index = ids.index(device.id)
        devices.pop(index)
        self.devices = devices

        if self.is_synced(device):
            self.unsync_device(device)


    def get_subscriptions_by_device(self, public=None):
        from mygpo.db.couchdb.podcast_state import subscriptions_by_user
        get_dev = itemgetter(2)
        groups = collections.defaultdict(list)
        subscriptions = subscriptions_by_user(self, public=public)
        subscriptions = sorted(subscriptions, key=get_dev)

        for public, podcast_id, device_id in subscriptions:
            groups[device_id].append(podcast_id)

        return groups


    def get_subscribed_podcast_states(self, public=None):
        """
        Returns the Ids of all subscribed podcasts
        """

        r = PodcastUserState.view('subscriptions/by_user',
                startkey     = [self._id, public, None, None],
                endkey       = [self._id+'ZZZ', None, None, None],
                reduce       = False,
                include_docs = True
            )

        return set(r)


    def get_subscribed_podcast_ids(self, public=None):
        states = self.get_subscribed_podcast_states(public=public)
        return [state.podcast for state in states]



    def get_subscribed_podcasts(self, public=None):
        """ Returns all subscribed podcasts for the user

        The attribute "url" contains the URL that was used when subscribing to
        the podcast """

        states = self.get_subscribed_podcast_states(public=public)
        podcast_ids = [state.podcast for state in states]
        podcasts = podcasts_to_dict(podcast_ids)

        for state in states:
            podcast = proxy_object(podcasts[state.podcast], url=state.ref_url)
            podcasts[state.podcast] = podcast

        return podcasts.values()



    def get_subscription_history(self, device_id=None, reverse=False, public=None):
        """ Returns chronologically ordered subscription history entries

        Setting device_id restricts the actions to a certain device
        """

        from mygpo.db.couchdb.podcast_state import podcast_states_for_user, \
            podcast_states_for_device

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
            podcast_states = podcast_states_for_user(self)
        else:
            podcast_states = podcast_states_for_device(device_id)

        # create an action_iter for each PodcastUserState
        subscription_action_lists = [action_iter(x) for x in podcast_states]

        action_cmp_key = lambda x: x.timestamp

        # Linearize their subscription-actions
        return linearize(action_cmp_key, subscription_action_lists, reverse)


    def get_global_subscription_history(self, public=None):
        """ Actions that added/removed podcasts from the subscription list

        Returns an iterator of all subscription actions that either
         * added subscribed a podcast that hasn't been subscribed directly
           before the action (but could have been subscribed) earlier
         * removed a subscription of the podcast is not longer subscribed
           after the action
        """

        subscriptions = collections.defaultdict(int)

        for entry in self.get_subscription_history(public=public):
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



    def get_newest_episodes(self, max_date, max_per_podcast=5):
        """ Returns the newest episodes of all subscribed podcasts

        Only max_per_podcast episodes per podcast are loaded. Episodes with
        release dates above max_date are discarded.

        This method returns a generator that produces the newest episodes.

        The number of required DB queries is equal to the number of (distinct)
        podcasts of all consumed episodes (max: number of subscribed podcasts),
        plus a constant number of initial queries (when the first episode is
        consumed). """

        cmp_key = lambda episode: episode.released or datetime(2000, 01, 01)

        podcasts = list(self.get_subscribed_podcasts())
        podcasts = filter(lambda p: p.latest_episode_timestamp, podcasts)
        podcasts = sorted(podcasts, key=lambda p: p.latest_episode_timestamp,
                        reverse=True)

        podcast_dict = dict((p.get_id(), p) for p in podcasts)

        # contains the un-yielded episodes, newest first
        episodes = []

        for podcast in podcasts:

            yielded_episodes = 0

            for episode in episodes:
                # determine for which episodes there won't be a new episodes
                # that is newer; those can be yielded
                if episode.released > podcast.latest_episode_timestamp:
                    p = podcast_dict.get(episode.podcast, None)
                    yield proxy_object(episode, podcast=p)
                    yielded_episodes += 1
                else:
                    break

            # remove the episodes that have been yielded before
            episodes = episodes[yielded_episodes:]

            # fetch and merge episodes for the next podcast
            from mygpo.db.couchdb.episode import episodes_for_podcast
            new_episodes = episodes_for_podcast(podcast, since=1,
                        until=max_date, descending=True, limit=max_per_podcast)
            episodes = sorted(episodes+new_episodes, key=cmp_key, reverse=True)


        # yield the remaining episodes
        for episode in episodes:
            podcast = podcast_dict.get(episode.podcast, None)
            yield proxy_object(episode, podcast=podcast)




    def save(self, *args, **kwargs):

        from mygpo.db.couchdb.podcast_state import podcast_states_for_user

        super(User, self).save(*args, **kwargs)

        podcast_states = podcast_states_for_user(self)
        for state in podcast_states:
            @repeat_on_conflict(['state'])
            def _update_state(state):
                old_devs = set(state.disabled_devices)
                state.set_device_state(self.devices)

                if old_devs != set(state.disabled_devices):
                    state.save()

            _update_state(state=state)




    def __eq__(self, other):
        if not other:
            return False

        # ensure that other isn't AnonymousUser
        return other.is_authenticated() and self._id == other._id


    def __ne__(self, other):
        return not(self == other)


    def __repr__(self):
        return 'User %s' % self._id


class History(object):

    def __init__(self, user, device):
        self.user = user
        self.device = device


    def __getitem__(self, key):

        if isinstance(key, slice):
            start = key.start or 0
            length = key.stop - start
        else:
            start = key
            length = 1

        if self.device:
            return device_history(self.user, self.device, start, length)

        else:
            return user_history(self.user, start, length)



class HistoryEntry(object):
    """ A class that can represent subscription and episode actions """


    @classmethod
    def from_action_dict(cls, action):

        entry = HistoryEntry()

        if 'timestamp' in action:
            ts = action.pop('timestamp')
            entry.timestamp = dateutil.parser.parse(ts)

        for key, value in action.items():
            setattr(entry, key, value)

        return entry


    @property
    def playmark(self):
        return getattr(self, 'position', None)


    @classmethod
    def fetch_data(cls, user, entries,
            podcasts=None, episodes=None):
        """ Efficiently loads additional data for a number of entries """

        if podcasts is None:
            # load podcast data
            podcast_ids = [getattr(x, 'podcast_id', None) for x in entries]
            podcast_ids = filter(None, podcast_ids)
            podcasts = podcasts_to_dict(podcast_ids)

        if episodes is None:
            from mygpo.db.couchdb.episode import episodes_to_dict
            # load episode data
            episode_ids = [getattr(x, 'episode_id', None) for x in entries]
            episode_ids = filter(None, episode_ids)
            episodes = episodes_to_dict(episode_ids)

        # load device data
        # does not need pre-populated data because no db-access is required
        device_ids = [getattr(x, 'device_id', None) for x in entries]
        device_ids = filter(None, device_ids)
        devices = dict([ (id, user.get_device(id)) for id in device_ids])


        for entry in entries:
            podcast_id = getattr(entry, 'podcast_id', None)
            entry.podcast = podcasts.get(podcast_id, None)

            episode_id = getattr(entry, 'episode_id', None)
            entry.episode = episodes.get(episode_id, None)

            if hasattr(entry, 'user'):
                entry.user = user

            device = devices.get(getattr(entry, 'device_id', None), None)
            entry.device = device


        return entries
