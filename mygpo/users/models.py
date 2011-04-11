import uuid, collections
from datetime import datetime
from couchdbkit import ResourceNotFound
from couchdbkit.ext.django.schema import *

from mygpo.core.models import Podcast
from mygpo.utils import linearize, get_to_dict
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
        return filter(lambda x: x.title, Podcast.get_multi(ids))


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
    timestamp     = DateTimeProperty(required=True)
    device_oldid  = IntegerProperty()
    started       = IntegerProperty()
    playmark      = IntegerProperty()
    total         = IntegerProperty()

    def __eq__(self, other):
        if not isinstance(other, EpisodeAction):
            return False
        vals = ('action', 'timestamp', 'device_oldid', 'started', 'playmark',
                'total')
        return all([getattr(self, v, None) == getattr(other, v, None) for v in vals])


    def __repr__(self):
        return '%s-Action on %s at %s (in %s)' % \
            (self.action, self.device_oldid, self.timestamp, self._id)


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
    actions       = SchemaListProperty(EpisodeAction)
    settings      = DictProperty()
    user_oldid    = IntegerProperty()
    ref_url       = StringProperty(required=True)
    podcast_ref_url = StringProperty(required=True)
    merged_ids    = StringListProperty()
    chapters      = SchemaListProperty(Chapter)


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
            state.episode = podcast.get_id()
            state.podcast = episode.podcast
            state.user_oldid = user.id
            state.ref_url = episode.url
            state.podcast_ref_url = podcast.url

            return state

    @classmethod
    def count(cls):
        r = cls.view('users/episode_states_by_user_episode',
            limit=0)
        return r.total_rows


    def add_actions(self, actions):
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
                self.chapters.append(chapter)

            for start, end in rem:
                print 'remove: start %d, end %d' % (start, end)
                keep = lambda c: c.start != start or c.end != end
                self.chapters = filter(keep, self.chapters)

            self.save()

        update(state=self)


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
            startkey=[self.podcast, self.user_oldid, None],
            endkey  =[self.podcast, self.user_oldid, {}])
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
            startkey=[self.oldid, public, None, None],
            endkey=[self.oldid+1, None, None, None])
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


    def __repr__(self):
        return 'User %s' % self._id


class HistoryEntry(object):

    @classmethod
    def fetch_data(cls, user, entries):
        """ Efficiently loads additional data for a number of entries """

        # load podcast data
        podcast_ids = [x.podcast_id for x in entries]
        podcasts = get_to_dict(Podcast, podcast_ids, get_id=Podcast.get_id)

        # load device data
        device_ids = [x.device_id for x in entries]
        devices = dict([ (id, user.get_device(id)) for id in device_ids])

        for entry in entries:
            entry.podcast = podcasts[entry.podcast_id]
            entry.device = devices[entry.device_id]
            entry.user = user

        return entries
