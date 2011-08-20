import uuid, collections
from datetime import datetime
import dateutil.parser
from itertools import imap
from couchdbkit import ResourceNotFound
from couchdbkit.ext.django.schema import *

from mygpo.core.proxy import proxy_object
from mygpo.core.models import Podcast, Episode
from mygpo.utils import linearize, get_to_dict, iterate_together
from mygpo.decorators import repeat_on_conflict


class Rating(DocumentSchema):
    rating = IntegerProperty()
    timestamp = DateTimeProperty(default=datetime.utcnow)


class Suggestions(Document):
    user = StringProperty()
    user_oldid = IntegerProperty()
    podcasts = StringListProperty()
    blacklist = StringListProperty()
    ratings = SchemaListProperty(Rating)

    @classmethod
    def for_user_oldid(cls, oldid):
        r = cls.view('users/suggestions_by_user_oldid', key=oldid, \
            include_docs=True)
        if r:
            return r.first()
        else:
            s = Suggestions()
            s.user_oldid = oldid
            return s


    def get_podcasts(self, count=None):
        user = User.for_oldid(self.user_oldid)
        subscriptions = user.get_subscribed_podcast_ids()

        ids = filter(lambda x: not x in self.blacklist + subscriptions, self.podcasts)
        if count:
            ids = ids[:count]
        return filter(lambda x: x and x.title, Podcast.get_multi(ids))


    def __repr__(self):
        if not self._id:
            return super(Suggestions, self).__repr__()
        else:
            return '%d Suggestions for %s (%s)' % \
                (len(self.podcasts),
                 self.user[:10] if self.user else self.user_oldid,
                 self._id[:10])


class EpisodeAction(DocumentSchema):
    """
    One specific action to an episode. Must
    always be part of a EpisodeUserState
    """

    action        = StringProperty(required=True)
    timestamp     = DateTimeProperty(required=True, default=datetime.utcnow)
    device_oldid  = IntegerProperty()
    device        = StringProperty()
    started       = IntegerProperty()
    playmark      = IntegerProperty()
    total         = IntegerProperty()

    def __eq__(self, other):
        if not isinstance(other, EpisodeAction):
            return False
        vals = ('action', 'timestamp', 'device_oldid', 'started', 'playmark',
                'total')
        return all([getattr(self, v, None) == getattr(other, v, None) for v in vals])


    def to_history_entry(self):
        entry = HistoryEntry()
        entry.action = self.action
        entry.timestamp = self.timestamp
        entry.device_oldid = self.device_oldid
        entry.device_id = self.device
        entry.started = self.started
        entry.position = self.playmark
        entry.total = self.total
        return entry


    @staticmethod
    def filter(user_oldid, since=None, until={}, podcast_id=None,
               device_oldid=None):
        """ Returns Episode Actions for the given criteria"""

        since_str = since.strftime('%Y-%m-%dT%H:%M:%S') if since else None
        until_str = until.strftime('%Y-%m-%dT%H:%M:%S') if until else {}

        # further parts of the key are filled in below
        startkey = [user_oldid, since_str, None, None]
        endkey   = [user_oldid, until_str, {}, {}]

        # additional filter that are carried out by the
        # application, not by the database
        add_filters = []

        if isinstance(podcast_id, basestring):
            if until is not None: # filter in database
                startkey[2] = podcast_id
                endkey[2]   = podcast_id

            add_filters.append( lambda x: x['podcast_id'] == podcast_id )

        elif isinstance(podcast_id, list):
            add_filters.append( lambda x: x['podcast_id'] in podcast_id )

        elif podcast_id is not None:
            raise ValueError('podcast_id can be either None, basestring '
                    'or a list of basestrings')


        if device_oldid:
            if None not in (until, podcast_id): # filter in database
                startkey[3] = device_oldid
                endkey[3]   = device_oldid
            else:
                add_filters.append( lambda x: x['device_oldid'] == device_oldid)


        db = EpisodeUserState.get_db()
        res = db.view('users/episode_actions',
                startkey = startkey,
                endkey   = endkey
            )

        for r in res:
            action = r['value']
            if all( f(action) for f in add_filters):
                yield action


    def validate_time_values(self):
        """ Validates allowed combinations of time-values """

        PLAY_ACTION_KEYS = ('playmark', 'started', 'total')

        # Key found, but must not be supplied (no play action!)
        if self.action != 'play':
            for key in PLAY_ACTION_KEYS:
                if getattr(self, key, None) is not None:
                    raise ValueError('%s only allowed in play actions' % key)

        # Sanity check: If started or total are given, require playmark
        if ((self.started is not None) or (self.total is not None)) and \
            self.playmark is None:
            raise ValueError('started and total require position')

        # Sanity check: total and playmark can only appear together
        if ((self.total is not None) or (self.started is not None)) and \
           ((self.total is None)     or (self.started is None)):
            raise ValueError('total and started can only appear together')


    def __repr__(self):
        return '%s-Action on %s at %s (in %s)' % \
            (self.action, self.device_oldid, self.timestamp, self._id)


    def __hash__(self):
        return hash(frozenset([self.action, self.timestamp, self.device_oldid, self.started, self.playmark, self.total]))


class Chapter(Document):
    """ A user-entered episode chapter """

    device = StringProperty()
    created = DateTimeProperty()
    start = IntegerProperty(required=True)
    end = IntegerProperty(required=True)
    label = StringProperty()
    advertisement = BooleanProperty()

    @classmethod
    def for_episode(cls, episode_id):
        db = cls.get_db()
        r = db.view('users/chapters_by_episode',
                startkey = [episode_id, None],
                endkey   = [episode_id, {}],
                wrap_doc = False,
            )

        for res in r:
            user = res['key'][1]
            chapter = Chapter.wrap(res['value'])
            yield (user, chapter)


    def __repr__(self):
        return '<%s %s (%d-%d)>' % (self.__class__.__name__, self.label,
                self.start, self.end)


class EpisodeUserState(Document):
    """
    Contains everything a user has done with an Episode
    """

    episode_oldid = IntegerProperty()
    episode       = StringProperty(required=True)
    podcast       = StringProperty()
    actions       = SchemaListProperty(EpisodeAction)
    settings      = DictProperty()
    user_oldid    = IntegerProperty()
    ref_url       = StringProperty(required=True)
    podcast_ref_url = StringProperty(required=True)
    merged_ids    = StringListProperty()
    chapters      = SchemaListProperty(Chapter)
    podcast       = StringProperty(required=True)


    @classmethod
    def for_user_episode(cls, user, episode):
        r = cls.view('users/episode_states_by_user_episode',
            key=[user.id, episode._id], include_docs=True)

        if r:
            return r.first()

        else:
            from mygpo import migrate
            new_user = migrate.get_or_migrate_user(user)
            podcast = Podcast.get(episode.podcast)

            state = EpisodeUserState()
            state.episode = episode._id
            state.podcast = episode.podcast
            state.user_oldid = user.id
            state.ref_url = episode.url
            state.podcast_ref_url = podcast.url

            return state

    @classmethod
    def for_ref_urls(cls, user, podcast_url, episode_url):
        res = cls.view('users/episode_states_by_ref_urls',
            key = [user.id, podcast_url, episode_url], limit=1, include_docs=True)
        if res:
            state = res.first()
            state.ref_url = episode_url
            state.podcast_ref_url = podcast_url
            return state
        else:
            from mygpo.api import models as oldmodels
            from mygpo import migrate

            old_p, _ = oldmodels.Podcast.objects.get_or_create(url=podcast_url)
            podcast = migrate.get_or_migrate_podcast(old_p)

            episode = Episode.for_podcast_id_url(podcast.get_id(), episode_url,
                    create=True)

            return episode.get_user_state(user)


    @classmethod
    def count(cls):
        r = cls.view('users/episode_states_by_user_episode',
            limit=0)
        return r.total_rows


    def add_actions(self, actions):
        map(EpisodeAction.validate_time_values, actions)
        self.actions = list(self.actions) + actions
        self.actions = list(set(self.actions))
        self.actions = sorted(self.actions, key=lambda x: x.timestamp)


    def is_favorite(self):
        return self.settings.get('is_favorite', False)


    def set_favorite(self, set_to=True):
        self.settings['is_favorite'] = set_to


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

        return (self.episode_oldid == other.episode_oldid and \
                self.episode == other.episode and
                self.actions == other.actions)



class SubscriptionAction(Document):
    action    = StringProperty()
    timestamp = DateTimeProperty(default=datetime.utcnow)
    device    = StringProperty()


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


class PodcastUserState(Document):
    """
    Contains everything that a user has done
    with a specific podcast and all its episodes
    """

    podcast       = StringProperty(required=True)
    episodes      = SchemaDictProperty(EpisodeUserState)
    user_oldid    = IntegerProperty()
    settings      = DictProperty()
    actions       = SchemaListProperty(SubscriptionAction)
    tags          = StringListProperty()
    ref_url       = StringProperty(required=True)
    disabled_devices = StringListProperty()
    merged_ids    = StringListProperty()


    @classmethod
    def for_user_podcast(cls, user, podcast):
        r = PodcastUserState.view('users/podcast_states_by_podcast', \
            key=[podcast.get_id(), user.id], limit=1, include_docs=True)
        if r:
            return r.first()
        else:
            from mygpo import migrate
            new_user = migrate.get_or_migrate_user(user)
            p = PodcastUserState()
            p.podcast = podcast.get_id()
            p.user_oldid = user.id
            p.ref_url = podcast.url
            p.settings['public_subscription'] = new_user.settings.get('public_subscriptions', True)

            for device in migrate.get_devices(user):
                p.set_device_state(device)

            return p


    @classmethod
    def for_user(cls, user):
        return cls.for_user_oldid(user.id)


    @classmethod
    def for_user_oldid(cls, user_oldid):
        r = PodcastUserState.view('users/podcast_states_by_user',
            startkey=[user_oldid, None], endkey=[user_oldid, 'ZZZZ'],
            include_docs=True)
        return list(r)


    @classmethod
    def for_device(cls, device_id):
        r = PodcastUserState.view('users/podcast_states_by_device',
            startkey=[device_id, None], endkey=[device_id, {}],
            include_docs=True)
        return list(r)


    def remove_device(self, device):
        """
        Removes all actions from the podcast state that refer to the
        given device
        """
        self.actions = filter(lambda a: a.device != device.id, self.actions)


    @classmethod
    def count(cls):
        r = PodcastUserState.view('users/podcast_states_by_user',
            limit=0)
        return r.total_rows


    def subscribe(self, device):
        action = SubscriptionAction()
        action.action = 'subscribe'
        action.device = device.id
        action.device_oldid = device.oldid
        self.add_actions([action])


    def unsubscribe(self, device):
        action = SubscriptionAction()
        action.action = 'unsubscribe'
        action.device = device.id
        action.device_oldid = device.oldid
        self.add_actions([action])


    def add_actions(self, actions):
        self.actions = list(set(self.actions + actions))
        self.actions = sorted(self.actions)


    def add_tags(self, tags):
        self.tags = list(set(self.tags + tags))


    def set_device_state(self, device):
        if device.deleted:
            self.disabled_devices = list(set(self.disabled_devices + [device.id]))
        elif not device.deleted and device.id in self.disabled_devices:
            self.disabled_devices.remove(device.id)


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
        r = PodcastUserState.view('users/subscriptions_by_podcast',
            startkey = [self.podcast, self.user_oldid, None],
            endkey   = [self.podcast, self.user_oldid, {}],
            reduce   = False,
            )
        return (res['key'][2] for res in r)


    def is_public(self):
        return self.settings.get('public_subscription', True)


    def __eq__(self, other):
        if other is None:
            return False

        return self.podcast == other.podcast and \
               self.user_oldid == other.user_oldid

    def __repr__(self):
        return 'Podcast %s for User %s (%s)' % \
            (self.podcast, self.user_oldid, self._id)


class Device(Document):
    id       = StringProperty(default=lambda: uuid.uuid4().hex)
    oldid    = IntegerProperty()
    uid      = StringProperty()
    name     = StringProperty()
    type     = StringProperty()
    settings = DictProperty()
    deleted  = BooleanProperty()

    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('users/devices_by_oldid', key=oldid)
        return r.first() if r else None


    def get_subscription_changes(self, since, until):
        """
        Returns the subscription changes for the device as two lists.
        The first lists contains the Ids of the podcasts that have been
        subscribed to, the second list of those that have been unsubscribed
        from.
        """

        add, rem = [], []
        podcast_states = PodcastUserState.for_device(self.id)
        for p_state in podcast_states:
            change = p_state.get_change_between(self.id, since, until)
            if change == 'subscribe':
                add.append( p_state.podcast )
            elif change == 'unsubscribe':
                rem.append( p_state.podcast )

        return add, rem


    def get_latest_changes(self):
        podcast_states = PodcastUserState.for_device(self.id)
        for p_state in podcast_states:
            actions = filter(lambda x: x.device == self.id, reversed(p_state.actions))
            if actions:
                yield (p_state.podcast, actions[0])


    def get_subscribed_podcast_ids(self):
        from mygpo.api.models import Device
        d = Device.objects.get(id=self.oldid)
        d.sync()
        r = self.view('users/subscribed_podcasts_by_device',
            startkey=[self.id, None],
            endkey=[self.id, {}])
        return [res['key'][1] for res in r]


    def get_subscribed_podcasts(self):
        return Podcast.get_multi(self.get_subscribed_podcast_ids())



def token_generator(length=32):
    import random, string
    return  "".join(random.sample(string.letters+string.digits, length))


class User(Document):
    oldid    = IntegerProperty()
    settings = DictProperty()
    devices  = SchemaListProperty(Device)
    published_objects = StringListProperty()

    # token for accessing subscriptions of this use
    subscriptions_token    = StringProperty(default=token_generator)

    # token for accessing the favorite-episodes feed of this user
    favorite_feeds_token   = StringProperty(default=token_generator)

    # token for automatically updating feeds published by this user
    publisher_update_token = StringProperty(default=token_generator)


    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('users/users_by_oldid', key=oldid, limit=1, include_docs=True)
        return r.one() if r else None


    def create_new_token(self, token_name, length=32):
        setattr(self, token_name, token_generator(length))


    def get_device(self, id):
        for device in self.devices:
            if device.id == id:
                return device

        return None


    def get_device_by_uid(self, uid):
        for device in self.devices:
            if device.uid == uid:
                return device


    def get_device_by_oldid(self, oldid):
        for device in self.devices:
            if device.oldid == oldid:
                return device


    def set_device(self, device):
        devices = list(self.devices)
        ids = [x.id for x in devices]
        if not device.id in ids:
            devices.append(device)
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


    def get_subscriptions(self, public=None):
        """
        Returns a list of (podcast-id, device-id) tuples for all
        of the users subscriptions
        """

        r = PodcastUserState.view('users/subscribed_podcasts_by_user',
            startkey = [self.oldid, public, None, None],
            endkey   = [self.oldid+1, None, None, None],
            reduce   = False,
            )
        return [res['key'][1:] for res in r]


    def get_subscribed_podcast_ids(self, public=None):
        """
        Returns the Ids of all subscribed podcasts
        """
        return list(set(x[1] for x in self.get_subscriptions(public=public)))


    def get_subscribed_podcasts(self, public=None):
        return Podcast.get_multi(self.get_subscribed_podcast_ids(public=public))


    def get_subscription_history(self, device_id=None, reverse=False, public=None):
        """ Returns chronologically ordered subscription history entries

        Setting device_id restricts the actions to a certain device
        """

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
            podcast_states = PodcastUserState.for_user_oldid(self.oldid)
        else:
            podcast_states = PodcastUserState.for_device(device_id)

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


    def get_newest_episodes(self, max_date):
        """ Returns the newest episodes of all subscribed podcasts

        Episodes with release dates above max_date are discarded"""


        podcasts = dict( (p.get_id(), p) for p in
                self.get_subscribed_podcasts())

        episodes = [p.get_episodes(until=max_date, descending=True) for p in
                podcasts.values()]

        cmp_key = lambda episode: episode.released

        for res in iterate_together(episodes, key=cmp_key, reverse=True):
            # res is a sparse tuple
            for episode in filter(None, res):
                podcast = podcasts.get(episode.podcast, None)
                yield proxy_object(episode, podcast=podcast)


    def __eq__(self, other):
        if not other:
            return False

        return self._id == other._id


    def __repr__(self):
        return 'User %s' % self._id


class History(object):

    def __init__(self, user, device):
        self.user = user
        self.device = device
        self._db = EpisodeUserState.get_db()

        if device:
            self._view = 'users/device_history'
            self._startkey = [self.user.oldid, device.oldid, None]
            self._endkey   = [self.user.oldid, device.oldid, {}]
        else:
            self._view = 'users/history'
            self._startkey = [self.user.oldid, None]
            self._endkey   = [self.user.oldid, {}]


    def __getitem__(self, key):

        if isinstance(key, slice):
            start = key.start or 0
            length = key.stop - start
        else:
            start = key
            length = 1

        res = self._db.view(self._view,
                descending = True,
                startkey   = self._endkey,
                endkey     = self._startkey,
                limit      = length,
                skip       = start,
            )

        for action in res:
            action = action['value']
            yield HistoryEntry.from_action_dict(action)



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
    def fetch_data(cls, user, entries):
        """ Efficiently loads additional data for a number of entries """

        # load podcast data
        podcast_ids = [getattr(x, 'podcast_id', None) for x in entries]
        podcast_ids = filter(None, podcast_ids)
        podcasts = get_to_dict(Podcast, podcast_ids, get_id=Podcast.get_id)

        # load episode data
        episode_ids = [getattr(x, 'episode_id', None) for x in entries]
        episode_ids = filter(None, episode_ids)
        episodes = get_to_dict(Episode, episode_ids)

        # load device data
        device_ids = [getattr(x, 'device_id', None) for x in entries]
        device_ids = filter(None, device_ids)
        devices = dict([ (id, user.get_device(id)) for id in device_ids])

        device_oldids = (getattr(x, 'device_oldid', None) for x in entries)
        device_oldids = filter(None, device_oldids)
        devices_oldids = dict([ (oldid, user.get_device_by_oldid(oldid)) for oldid in device_oldids])

        for entry in entries:
            podcast_id = getattr(entry, 'podcast_id', None)
            entry.podcast = podcasts.get(podcast_id, None)

            episode_id = getattr(entry, 'episode_id', None)
            entry.episode = episodes.get(episode_id, None)
            entry.user = user

            device = devices.get(getattr(entry, 'device_id', None), None) or \
                     devices_oldids.get(getattr(entry, 'device_oldid', None), None)
            entry.device = device


        return entries
