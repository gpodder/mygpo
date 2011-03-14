import hashlib
from couchdbkit.ext.django.schema import *
from mygpo import utils


class Episode(Document):
    """
    Represents an Episode. Can only be part of a Podcast
    """

    title = StringProperty()
    description = StringProperty()
    link = StringProperty()
    released = DateTimeProperty()
    author = StringProperty()
    duration = IntegerProperty()
    filesize = IntegerProperty()
    language = StringProperty()
    last_update = DateTimeProperty()
    outdated = BooleanProperty()
    mimetypes = StringListProperty()
    merged_ids = StringListProperty()
    oldid = IntegerProperty()
    urls = StringListProperty()
    # when accessed via a view, a podcast attribute is added
    # that contains the id of the podcast


    @classmethod
    def get_multi(cls, ids):
        r = cls.view('_all_docs', include_docs=True, keys=ids)
        return list(r)

    @classmethod
    def for_oldid(self, oldid):
        r = Episode.view('core/episodes_by_oldid', key=oldid, limit=1, include_docs=True)
        return r.one() if r else None


    def get_old_obj(self):
        if self.oldid:
            from mygpo.api.models import Episode
            return Episode.objects.get(id=self.oldid)
        return None

    @property
    def url(self):
        return self.urls[0]


    def __repr__(self):
        return 'Episode %s' % self._id


    def __eq__(self, other):
        if other == None:
            return False
        return self.id == other.id


class SubscriberData(DocumentSchema):
    timestamp = DateTimeProperty()
    subscriber_count = IntegerProperty()

    def __eq__(self, other):
        if not isinstance(other, SubscriberData):
            return False

        return (self.timestamp == other.timestamp) and \
               (self.subscriber_count == other.subscriber_count)


class PodcastSubscriberData(Document):
    podcast = StringProperty()
    subscribers = SchemaListProperty(SubscriberData)

    @classmethod
    def for_podcast(cls, id):
        r = cls.view('core/subscribers_by_podcast', key=id, include_docs=True)
        if r:
            return r.first()

        data = PodcastSubscriberData()
        data.podcast = id
        return data

    def __repr__(self):
        return 'PodcastSubscriberData for Podcast %s (%s)' % (self.podcast, self._id)


class Podcast(Document):
    id = StringProperty()
    title = StringProperty()
    urls = StringListProperty()
    description = StringProperty()
    link = StringProperty()
    last_update = DateTimeProperty()
    logo_url = StringProperty()
    author = StringProperty()
    merged_ids = StringListProperty()
    oldid = IntegerProperty()
    group = StringProperty()
    group_member_name = StringProperty()
    related_podcasts = StringListProperty()
    subscribers = SchemaListProperty(SubscriberData)
    language = StringProperty()
    content_types = StringListProperty()
    tags = DictProperty()


    @classmethod
    def get(cls, id):
        r = cls.view('core/podcasts_by_id', key=id)
        return r.first() if r else None


    @classmethod
    def get_multi(cls, ids):
        r = cls.view('core/podcasts_by_id', keys=ids)
        return list(r)


    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('core/podcasts_by_oldid', key=long(oldid))
        return r.first() if r else None


    @classmethod
    def for_url(cls, url):
        r = cls.view('core/podcasts_by_url', key=url)
        return r.first() if r else None


    def get_id(self):
        return self.id or self._id

    @property
    def display_title(self):
        return self.title or self.url

    def get_episodes(self):
        return list(Episode.view('core/episodes_by_podcast', key=self.get_id(), include_docs=True))


    @property
    def url(self):
        return self.urls[0]


    def get_logo_url(self, size):
        if self.logo_url:
            sha = hashlib.sha1(self.logo_url).hexdigest()
            return '/logo/%d/%s.jpg' % (size, sha)
        return '/media/podcast-%d.png' % (hash(self.title) % 5, )


    def subscriber_count(self):
        if not self.subscribers:
            return 0
        return self.subscribers[-1].subscriber_count


    def prev_subscriber_count(self):
        if len(self.subscribers) < 2:
            return 0
        return self.subscribers[-2].subscriber_count


    def get_user_state(self, user):
        from mygpo.users.models import PodcastUserState
        return PodcastUserState.for_user_podcast(user, self)


    def get_all_states(self):
        from mygpo.users.models import PodcastUserState
        return PodcastUserState.view('users/podcast_states_by_podcast',
            startkey = [self.get_id(), None],
            endkey   = [self.get_id(), '\ufff0'],
            include_docs=True)


    def subscribe(self, device):
        from mygpo import migrate
        state = self.get_user_state(device.user)
        device = migrate.get_or_migrate_device(device)
        state.subscribe(device)
        state.save()


    def unsubscribe(self, device):
        from mygpo import migrate
        state = self.get_user_state(device.user)
        device = migrate.get_or_migrate_device(device)
        state.unsubscribe(device)
        state.save()


    def subscribe_targets(self, user):
        """
        returns all Devices and SyncGroups on which this podcast can be subsrbied. This excludes all
        devices/syncgroups on which the podcast is already subscribed
        """
        targets = []

        from mygpo.api.models import Device
        from mygpo import migrate

        devices = Device.objects.filter(user=user, deleted=False)
        for d in devices:
            dev = migrate.get_or_migrate_device(d)
            subscriptions = dev.get_subscribed_podcasts()
            if self in subscriptions: continue

            if d.sync_group:
                if not d.sync_group in targets: targets.append(d.sync_group)
            else:
                targets.append(d)

        return targets


    def all_tags(self):
        """
        Returns all tags that are stored for the podcast, in decreasing order of importance
        """

        res = Podcast.view('directory/tags_by_podcast', startkey=[self.get_id(), None],
            endkey=[self.get_id(), 'ZZZZZZ'], reduce=True, group=True, group_level=2)
        tags = sorted(res.all(), key=lambda x: x['value'], reverse=True)
        return [x['key'][1] for x in tags]


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
            if self in group.podcasts:
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
    title    = StringProperty()
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

    @property
    def display_title(self):
        return self.title

    @property
    def logo_url(self):
        return utils.first(p.logo_url for p in self.podcasts)


    def get_logo_url(self, size):
        if self.logo_url:
            sha = hashlib.sha1(self.logo_url).hexdigest()
            return '/logo/%d/%s.jpg' % (size, sha)
        return '/media/podcast-%d.png' % (hash(self.title) % 5, )


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


class SanitizingRule(Document):
    slug        = StringProperty()
    applies_to  = StringListProperty()
    search      = StringProperty()
    replace     = StringProperty()
    priority    = IntegerProperty()
    description = StringProperty()


    @classmethod
    def for_obj_type(cls, obj_type):
        r = cls.view('core/sanitizing_rules_by_target', include_docs=True,
            startkey=[obj_type, None], endkey=[obj_type, {}])
        return list(r)


    @classmethod
    def for_slug(cls, slug):
        r = cls.view('core/sanitizing_rules_by_slug', include_docs=True,
            key=slug)
        return r.one() if r else None


    def __repr__(self):
        return 'SanitizingRule %s' % self._id
