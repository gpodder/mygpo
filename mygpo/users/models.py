import uuid
from datetime import datetime
from couchdbkit import ResourceNotFound
from couchdbkit.ext.django.schema import *

from mygpo.core.models import Podcast


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
        from mygpo.api.models import Subscription
        subscriptions = [x.podcast for x in Subscription.objects.filter(user__id=self.user_oldid)]
        subscriptions = [Podcast.for_oldid(x.id) for x in subscriptions]
        subscriptions = [x._id for x in subscriptions if x]

        ids = filter(lambda x: not x in self.blacklist + subscriptions, self.podcasts)
        if count:
            ids = ids[:count]
        return Podcast.get_multi(ids)


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


    @classmethod
    def for_user_episode(cls, user_oldid, episode_id):
        r = cls.view('users/episode_states_by_user_episode',
            key=[user_oldid, episode_id], include_docs=True)
        return r.first() if r else None


    @classmethod
    def count(cls):
        r = cls.view('users/episode_states_by_user_episode',
            limit=0)
        return r.total_rows


    def add_actions(self, actions):
        self.actions += actions
        self.actions = list(set(self.actions))
        self.actions.sort(key=lambda x: x.timestamp)


    def is_favorite(self):
        return self.settings.get('is_favorite', False)


    def set_favorite(self, set_to=True):
        self.settings['is_favorite'] = set_to


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

    def __eq__(self, other):
        return self.actions == other.action and \
               self.timestamp == other.timestamp and \
               self.device == other.device


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


    @classmethod
    def for_user_podcast(cls, user, podcast):
        r = PodcastUserState.view('users/podcast_states_by_podcast', \
            key=[podcast.get_id(), user.id], limit=1, include_docs=True)
        if r:
            return r.first()
        else:
            p = PodcastUserState()
            p.podcast = podcast.get_id()
            p.user_oldid = user.id
            p.ref_url = podcast.url
            return p


    @classmethod
    def for_user(cls, user):
        r = PodcastUserState.view('users/podcast_states_by_user',
            startkey=[user.id, None], endkey=[user.id, 'ZZZZ'],
            include_docs=True)
        return list(r)


    @classmethod
    def count(cls):
        r = PodcastUserState.view('users/podcast_states_by_user',
            limit=0)
        return r.total_rows


    def add_actions(self, actions):
        self.actions += actions
        self.actions = list(set(self.actions))
        self.actions.sort(key=lambda x: x.timestamp)


    def add_tags(self, tags):
        self.tags = list(set(self.tags + tags))


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

    @classmethod
    def for_user_uid(cls, user, uid):
        r = cls.view('users/devices_by_user_uid', key=[user.id, uid], limit=1)
        return r.one() if r else None


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


    def get_device(self, uid):
        for device in self.devices:
            if device.uid == uid:
                return device

        return None


    def __repr__(self):
        return 'User %s' % self._id
