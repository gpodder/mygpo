import uuid
from datetime import datetime
from couchdbkit import ResourceNotFound
from couchdbkit.ext.django.schema import *

from mygpo import utils


class Episode(Document):
    """
    Represents an Episode. Can only be part of a Podcast
    """

    id = StringProperty(default=lambda: uuid.uuid4().hex)
    oldid = IntegerProperty()
    urls = StringListProperty()

    @classmethod
    def for_id(cls, id):
        r = cls.view('core/episodes_by_id', key=id, limit=1, wrap_doc=False)
        return r.one() if r else None


    @classmethod
    def for_oldid(self, oldid):
        r = Episode.view('core/episodes_by_oldid', key=oldid, limit=1, wrap_doc=False)
        return r.one() if r else None


    def get_old_obj(self):
        if self.oldid:
            from mygpo.api.models import Episode
            return Episode.objects.get(id=self.oldid)
        return None


    def __repr__(self):
        return 'Episode %s (in %s)' % \
            (self.id, self._id)


class SubscriberData(DocumentSchema):
    timestamp = DateTimeProperty()
    subscriber_count = IntegerProperty()

    def __eq__(self, other):
        if not isinstance(other, SubscriberData):
            return False

        return (self.timestamp == other.timestamp) and \
               (self.subscriber_count == other.subscriber_count)


class Podcast(Document):
    id = StringProperty()
    oldid = IntegerProperty()
    group = StringProperty()
    related_podcasts = StringListProperty()
    episodes = SchemaDictProperty(Episode)
    subscribers = SchemaListProperty(SubscriberData)
    language = StringProperty()
    content_types = StringListProperty()

    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('core/podcasts_by_oldid', key=long(oldid))
        return r.first() if r else None


    def get_id(self):
        return self.id or self._id


    def subscriber_count(self):
        if not self.subscribers:
            return 0
        return self.subscribers[-1].subscriber_count


    def prev_subscriber_count(self):
        if len(self.subscribers) < 2:
            return 0
        return self.subscribers[-2].subscriber_count


    def get_user_state(self, user):
        return PodcastUserState.for_user_podcast(user, self)


    def get_old_obj(self):
        if self.oldid:
            from mygpo.api.models import Podcast
            return Podcast.objects.get(id=self.oldid)
        return None


    def __repr__(self):
        if not self._id:
            return super(Podcast, self).__repr__()
        elif self.oldid:
            return '%s %s (%s)' % (self.__class__.__name__, self.get_id(), self.oldid)
        else:
            return '%s %s' % (self.__class__.__name__, self.get_id())


    def save(self):
        group = getattr(self, 'group', None)
        if group: #we are part of a PodcastGroup
            group = PodcastGroup.get(group)
            i = group.podcasts.index(self)
            group.podcasts[i] = self
            group.save()

        else:
            super(Podcast, self).save()


    def delete(self):
        group = getattr(self, 'group', None)
        if group:
            group = PodcastGroup.get(group)
            i = group.podcasts.index(self)
            del group.podcasts[i]
            group.save()

        else:
            super(Podcast, self).delete()

    @classmethod
    def all_podcasts_groups(cls):
        return cls.view('core/podcasts_groups', include_docs=True,
            classes=[Podcast, PodcastGroup]).iterator()


    def __eq__(self, other):
        if not self.get_id():
            return self == other

        if other == None:
            return False

        return self.get_id() == other.get_id()


class PodcastGroup(Document):
    podcasts = SchemaListProperty(Podcast)

    def get_id(self):
        return self._id

    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('core/podcastgroups_by_oldid', \
            key=oldid, limit=1, include_docs=True)
        return r.first() if r else None

    def subscriber_count(self):
        return sum([p.subscriber_count() for p in self.podcasts])


    def prev_subscriber_count(self):
        return sum([p.prev_subscriber_count() for p in self.podcasts])


    def add_podcast(self, podcast):
        podcast.id = podcast._id

        if not self._id:
            raise ValueError('group has to have an _id first')

        podcast.delete()
        podcast.group = self._id
        self.podcasts.append(podcast)
        self.save()
        return self.podcasts[-1]

    def get_old_obj(self):
        from mygpo.api.models import PodcastGroup
        return PodcastGroup.objects.get(id=self.oldid) if self.oldid else None


    def __repr__(self):
        if not self._id:
            return super(PodcastGroup, self).__repr__()
        elif self.oldid:
            return '%s %s (%s)' % (self.__class__.__name__, self._id[:10], self.oldid)
        else:
            return '%s %s' % (self.__class__.__name__, self._id[:10])


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
        r = cls.view('core/suggestions_by_user_oldid', key=oldid, \
            include_docs=True)
        if r:
            return r.first()
        else:
            s = Suggestions()
            s.user_oldid = oldid
            return s


    def get_podcasts(self):
        from mygpo.api.models import Subscription
        subscriptions = [x.podcast for x in Subscription.objects.filter(user__id=self.user_oldid)]
        subscriptions = [Podcast.for_oldid(x.id) for x in subscriptions]
        subscriptions = [x._id for x in subscriptions if x]

        for p in self.podcasts:
            if not p in self.blacklist and not p in subscriptions:
                try:
                    podcast = Podcast.get(p)
                except ResourceNotFound:
                    continue

                if podcast:
                    yield podcast


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


class PodcastUserState(Document):
    """
    Contains everything that a user has done
    with a specific podcast and all its episodes
    """

    podcast       = StringProperty(required=True)
    episodes      = SchemaDictProperty(EpisodeUserState)
    user_oldid    = IntegerProperty()
    settings      = DictProperty()

    @classmethod
    def for_user_podcast(cls, user, podcast):
        r = PodcastUserState.view('core/podcast_states_by_podcast', \
            key=[podcast.get_id(), user.id], limit=1, include_docs=True)
        if r:
            return r.first()
        else:
            p = PodcastUserState()
            p.podcast = podcast.get_id()
            p.user_oldid = user.id
            return p


    def get_episode(self, e_id):
        if e_id in self.episodes:
            return self.episodes[e_id]

        e = EpisodeUserState()
        e.episode = e_id
        self.episodes[e_id] = e
        return e

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
        r = cls.view('core/devices_by_user_uid', key=[user.id, uid], limit=1)
        return r.one() if r else None


class User(Document):
    oldid    = IntegerProperty()
    settings = DictProperty()
    devices  = SchemaListProperty(Device)


    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('core/users_by_oldid', key=oldid, limit=1, include_docs=True)
        return r.one() if r else None


    def get_device(self, uid):
        for device in self.devices:
            if device.uid == uid:
                return device

        return None
