import uuid
from datetime import datetime
from couchdbkit import ResourceNotFound
from couchdbkit.ext.django.schema import *


class Episode(Document):
    """
    Represents an Episode. Can only be part of a Podcast
    """

    id = StringProperty(default=lambda: uuid.uuid4().hex)
    oldid = IntegerProperty()
    urls = StringListProperty()

    @classmethod
    def for_oldid(self, oldid):
        r = Episode.view('core/episodes_by_oldid', key=oldid, limit=1, wrap_doc=False)
        return r.one() if r else None

    def __repr__(self):
        return 'Episode %s (in %s)' % \
            (self.id, self._id)


class Podcast(Document):
    id = StringProperty()
    oldid = IntegerProperty()
    group = StringProperty()
    related_podcasts = StringListProperty()
    episodes = SchemaDictProperty(Episode)

    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('core/podcasts_by_oldid', key=long(oldid))
        return r.first() if r else None


    def get_id(self):
        return getattr(self, 'id', None) or self._id

    def get_old_obj(self):
        if self.oldid:
            from mygpo.api.models import Podcast
            return Podcast.objects.get(id=self.oldid)
        return None


    def __repr__(self):
        if not self._id:
            return super(Podcast, self).__repr__()
        elif self.oldid:
            return '%s %s (%s)' % (self.__class__.__name__, self._id[:10], self.oldid)
        else:
            return '%s %s' % (self.__class__.__name__, self._id[:10])


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


    def __eq__(self, other):
        if not self.get_id():
            return self == other

        if other == None:
            return False

        return self.get_id() == other.get_id()



class PodcastGroup(Document):
    podcasts = SchemaListProperty(Podcast)

    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('core/podcastgroups_by_oldid', \
            key=oldid, limit=1, include_docs=True)
        return r.first() if r else None


    def add_podcast(self, podcast):
        podcast.id = podcast._id

        if not self._id:
            raise ValueError('group has to have an _id first')

        podcast.group = self._id
        self.podcasts.append(podcast)
        self.save()
        podcast.delete()


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


class EpisodeUserState(DocumentSchema):
    """
    Contains everything a user has done with an Episode
    """

    episode_oldid = IntegerProperty()
    episode       = StringProperty(required=True)
    actions       = SchemaListProperty(EpisodeAction)


    def add_actions(self, actions):
        self.actions += actions
        self.actions = list(set(self.actions))
        self.actions.sort(key=lambda x: x.timestamp)


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
        return e

    def __repr__(self):
        return 'Podcast %s for User %s (%s)' % \
            (self.podcast, self.user_oldid, self._id)
