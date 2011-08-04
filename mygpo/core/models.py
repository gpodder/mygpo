import hashlib
from datetime import datetime
from dateutil import parser

from couchdbkit.ext.django.schema import *

from mygpo.decorators import repeat_on_conflict
from mygpo import utils
from mygpo.core.proxy import DocumentABCMeta



class Episode(Document):
    """
    Represents an Episode. Can only be part of a Podcast
    """

    __metaclass__ = DocumentABCMeta

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
    podcast = StringProperty(required=True)
    listeners = IntegerProperty()
    content_types = StringListProperty()
    slug = StringProperty()
    merged_slugs = StringListProperty()


    @classmethod
    def get(cls, id):
        r = cls.view('core/episodes_by_id',
                key=id,
                include_docs=True,
            )
        return r.first() if r else None


    @classmethod
    def get_multi(cls, ids):
        return cls.view('core/episodes_by_id',
                include_docs=True,
                keys=ids
            )


    @classmethod
    def for_oldid(self, oldid):
        r = Episode.view('core/episodes_by_oldid', key=oldid, limit=1, include_docs=True)
        return r.one() if r else None


    @classmethod
    def for_slug(cls, podcast_id, slug):
        r = cls.view('core/episodes_by_slug',
                key          = [podcast_id, slug],
                include_docs = True
            )
        return r.first() if r else None


    @classmethod
    def for_podcast_url(cls, podcast_url, episode_url, create=False):
        podcast = Podcast.for_url(podcast_url)
        return cls.for_podcast_id_url(podcast.get_id(), episode_url, create)


    @classmethod
    def for_podcast_id_url(cls, podcast_id, episode_url, create=False):
        r = cls.view('core/episodes_by_podcast_url',
                key          = [podcast_id, episode_url],
                include_docs = True,
            )

        if r:
            return r.first()

        if create:
            episode = Episode()
            episode.podcast = podcast_id
            episode.urls = [episode_url]
            episode.save()
            return episode

        return None


    @classmethod
    def for_slug_id(cls, p_slug_id, e_slug_id):
        """ Returns the Episode for Podcast Slug/Id and Episode Slug/Id """

        # The Episode-Id is unique, so take that
        if utils.is_couchdb_id(e_slug_id):
            return cls.get(e_slug_id)

        # If we search using a slug, we need the Podcast's Id
        if utils.is_couchdb_id(p_slug_id):
            p_id = p_slug_id
        else:
            podcast = Podcast.get(p_slug_id)
            p_id = podcast.get_id()

        return cls.for_slug(p_id, e_slug_id)


    def get_user_state(self, user):
        from mygpo.users.models import EpisodeUserState
        return EpisodeUserState.for_user_episode(user, self)


    @property
    def url(self):
        return self.urls[0]

    def __repr__(self):
        return 'Episode %s' % self._id


    def listener_count(self, start=None, end={}):
        """ returns the number of users that have listened to this episode """

        from mygpo.users.models import EpisodeUserState
        r = EpisodeUserState.view('users/listeners_by_episode',
                startkey    = [self._id, start],
                endkey      = [self._id, end],
                reduce      = True,
                group       = True,
                group_level = 1
            )
        return r.first()['value'] if r else 0


    def listener_count_timespan(self, start=None, end={}):
        """ returns (date, listener-count) tuples for all days w/ listeners """

        from mygpo.users.models import EpisodeUserState
        r = EpisodeUserState.view('users/listeners_by_episode',
                startkey    = [self._id, start],
                endkey      = [self._id, end],
                reduce      = True,
                group       = True,
                group_level = 2,
            )

        for res in r:
            date = parser.parse(res['key'][1]).date()
            listeners = res['value']
            yield (date, listeners)


    @classmethod
    def count(cls):
        r = cls.view('core/episodes_by_podcast', limit=0)
        return r.total_rows


    @classmethod
    def all(cls):
        return utils.multi_request_view(cls, 'core/episodes_by_podcast',
                include_docs=True)

    def __eq__(self, other):
        if other == None:
            return False
        return self._id == other._id


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

    __metaclass__ = DocumentABCMeta

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
    slug = StringProperty()
    merged_slugs = StringListProperty()


    @classmethod
    def get(cls, id):
        r = cls.view('core/podcasts_by_id',
                key=id,
                classes=[Podcast, PodcastGroup],
                include_docs=True,
            )

        if not r:
            return None

        podcast_group = r.first()
        return podcast_group.get_podcast_by_id(id)


    @classmethod
    def for_slug(cls, slug):
        db = cls.get_db()
        r = db.view('core/podcasts_by_slug',
                startkey     = [slug, None],
                endkey       = [slug, {}],
                include_docs = True,
            )

        if not r:
            return None

        res = r.first()
        doc = res['doc']
        if doc['doc_type'] == 'Podcast':
            return Podcast.wrap(doc)
        else:
            pid = res['key'][1]
            pg = PodcastGroup.wrap(doc)
            return pg.get_podcast_by_id(pid)


    @classmethod
    def for_slug_id(cls, slug_id):
        """ Returns the Podcast for either an CouchDB-ID for a Slug """

        if utils.is_couchdb_id(slug_id):
            return cls.get(slug_id)
        else:
            return cls.for_slug(slug_id)


    @classmethod
    def get_multi(cls, ids):
        db = Podcast.get_db()
        r = db.view('core/podcasts_by_id',
                keys=ids,
                include_docs=True,
            )

        for res in r:
            if res['doc']['doc_type'] == 'Podcast':
                yield Podcast.wrap(res['doc'])
            else:
                pg = PodcastGroup.wrap(res['doc'])
                id = res['key']
                yield pg.get_podcast_by_id(id)


    @classmethod
    def for_oldid(cls, oldid):
        r = cls.view('core/podcasts_by_oldid',
                key=long(oldid),
                classes=[Podcast, PodcastGroup],
                include_docs=True
            )

        if not r:
            return None

        podcast_group = r.first()
        return podcast_group.get_podcast_by_oldid(oldid)


    @classmethod
    def for_url(cls, url, create=False):
        r = cls.view('core/podcasts_by_url',
                key=url,
                classes=[Podcast, PodcastGroup],
                include_docs=True
            )

        if r:
            podcast_group = r.first()
            return podcast_group.get_podcast_by_url(url)

        if create:
            podcast = cls()
            podcast.urls = [url]
            podcast.save()
            return podcast

        return None


    def get_podcast_by_id(self, _):
        return self
    get_podcast_by_oldid = get_podcast_by_id
    get_podcast_by_url = get_podcast_by_id


    def get_id(self):
        return self.id or self._id

    @property
    def display_title(self):
        return self.title or self.url


    def get_episodes(self, since=None, until={}, **kwargs):

        if kwargs.get('descending', False):
            since, until = until, since

        if isinstance(since, datetime):
            since = since.isoformat()

        if isinstance(until, datetime):
            until = until.isoformat()

        return Episode.view('core/episodes_by_podcast',
                startkey = [self.get_id(), since],
                endkey   = [self.get_id(), until],
                include_docs=True,
                **kwargs
            )


    def get_latest_episode(self):
        # since = 1 ==> has a timestamp
        episodes = list(self.get_episodes(since=1, descending=True, limit=1))
        return episodes[0] if episodes else None


    def get_episode_before(self, episode):
        if not episode.released:
            return None

        prevs = self.get_episodes(until=episode.released, descending=True,
                limit=1)
        prev = prevs.first() if prevs else None


    def get_episode_after(self, episode):
        if not episode.released:
            return None

        nexts = self.get_episodes(since=episode.released, limit=1)
        next = nexts.first() if nexts else None


    def get_episode_for_slug(self, slug):
        return Episode.for_slug(self.get_id(), slug)


    @property
    def url(self):
        return self.urls[0]


    def get_podcast(self):
        return self


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


    @repeat_on_conflict()
    def subscribe(self, device):
        from mygpo import migrate
        state = self.get_user_state(device.user)
        device = migrate.get_or_migrate_device(device)
        state.subscribe(device)
        state.save()


    @repeat_on_conflict()
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


    def listener_count(self):
        """ returns the number of users that have listened to this podcast """

        from mygpo.users.models import EpisodeUserState
        r = EpisodeUserState.view('users/listeners_by_podcast',
                startkey    = [self.get_id(), None],
                endkey      = [self.get_id(), {}],
                group       = True,
                group_level = 1,
                reduce      = True,
            )
        return r.first()['value']


    def listener_count_timespan(self, start=None, end={}):
        """ returns (date, listener-count) tuples for all days w/ listeners """

        from mygpo.users.models import EpisodeUserState
        r = EpisodeUserState.view('users/listeners_by_podcast',
                startkey    = [self.get_id(), start],
                endkey      = [self.get_id(), end],
                group       = True,
                group_level = 2,
                reduce      = True,
            )

        for res in r:
            date = parser.parse(res['key'][1]).date()
            listeners = res['value']
            yield (date, listeners)


    def episode_listener_counts(self):
        """ (Episode-Id, listener-count) tuples for episodes w/ listeners """

        from mygpo.users.models import EpisodeUserState
        r = EpisodeUserState.view('users/listeners_by_podcast_episode',
                startkey    = [self.get_id(), None, None],
                endkey      = [self.get_id(), {},   {}],
                group       = True,
                group_level = 2,
                reduce      = True,
            )

        for res in r:
            episode   = res['key'][1]
            listeners = res['value']
            yield (episode, listeners)


    def get_episode_states(self, user_oldid):
        """ Returns the latest episode actions for the podcast's episodes """

        from mygpo.users.models import EpisodeUserState
        db = EpisodeUserState.get_db()

        res = db.view('users/episode_states',
                startkey= [user_oldid, self.get_id(), None],
                endkey  = [user_oldid, self.get_id(), {}]
            )

        for r in res:
            action = r['value']
            yield action


    def get_old_obj(self):
        if self.oldid:
            from mygpo.api.models import Podcast
            return Podcast.objects.get(id=self.oldid)
        return None


    def __hash__(self):
        return hash(self.get_id())


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
            podcasts = list(group.podcasts)

            if not self in podcasts:
                # the podcast has not been added to the group correctly
                group.add_podcast(self)

            else:
                i = podcasts.index(self)
                podcasts[i] = self
                group.podcasts = podcasts
                group.save()

            i = podcasts.index(self)
            podcasts[i] = self
            group.podcasts = podcasts
            group.save()

        else:
            super(Podcast, self).save()


    def delete(self):
        group = getattr(self, 'group', None)
        if group:
            group = PodcastGroup.get(group)
            podcasts = list(group.podcasts)

            if self in podcasts:
                i = podcasts.index(self)
                del podcasts[i]
                group.podcasts = podcasts
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


    @classmethod
    def all_podcasts(cls):
        from mygpo.utils import multi_request_view

        for r in multi_request_view(cls, 'core/podcasts_by_oldid', wrap=False, include_docs=True):
            obj = r['doc']
            if obj['doc_type'] == 'Podcast':
                yield Podcast.wrap(obj)
            else:
                oldid = r[u'key']
                pg = PodcastGroup.wrap(obj)
                podcast = pg.get_podcast_by_oldid(oldid)
                yield podcast



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

    def get_podcast_by_id(self, id):
        for podcast in self.podcasts:
            if podcast.get_id() == id:
                return podcast
            if id in podcast.merged_ids:
                return podcast


    def get_podcast_by_oldid(self, oldid):
        for podcast in self.podcasts:
            if podcast.oldid == oldid:
                return podcast


    def get_podcast_by_url(self, url):
        for podcast in self.podcasts:
            if url in list(podcast.urls):
                return podcast


    def subscriber_count(self):
        return sum([p.subscriber_count() for p in self.podcasts])


    def prev_subscriber_count(self):
        return sum([p.prev_subscriber_count() for p in self.podcasts])

    @property
    def display_title(self):
        return self.title


    def get_podcast(self):
        # return podcast with most subscribers (bug 1390)
        return sorted(self.podcasts, key=Podcast.subscriber_count,
                reverse=True)[0]


    @property
    def logo_url(self):
        return utils.first(p.logo_url for p in self.podcasts)


    def get_logo_url(self, size):
        if self.logo_url:
            sha = hashlib.sha1(self.logo_url).hexdigest()
            return '/logo/%d/%s.jpg' % (size, sha)
        return '/media/podcast-%d.png' % (hash(self.title) % 5, )


    def add_podcast(self, podcast):
        if not podcast.id:
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


class SanitizingRuleStub(object):
    pass

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

        for rule in r:
            obj = SanitizingRuleStub()
            obj.slug = rule.slug
            obj.applies_to = list(rule.applies_to)
            obj.search = rule.search
            obj.replace = rule.replace
            obj.priority = rule.priority
            obj.description = rule.description
            yield obj


    @classmethod
    def for_slug(cls, slug):
        r = cls.view('core/sanitizing_rules_by_slug', include_docs=True,
            key=slug)
        return r.one() if r else None


    def __repr__(self):
        return 'SanitizingRule %s' % self._id
