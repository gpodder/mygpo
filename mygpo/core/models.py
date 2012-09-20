from __future__ import division

import hashlib
import os.path
import re
from datetime import datetime
from dateutil import parser
from random import randint, random

from couchdbkit.ext.django.schema import *
from restkit.errors import Unauthorized

from django.conf import settings
from django.core.urlresolvers import reverse

from mygpo.decorators import repeat_on_conflict
from mygpo import utils
from mygpo.cache import cache_result
from mygpo.couch import get_main_database
from mygpo.core.proxy import DocumentABCMeta
from mygpo.core.slugs import SlugMixin
from mygpo.core.oldid import OldIdMixin
from mygpo.web.logo import CoverArt


class SubscriptionException(Exception):
    pass


class MergedIdException(Exception):
    """ raised when an object is accessed through one of its merged_ids """

    def __init__(self, obj, current_id):
        self.obj = obj
        self.current_id = current_id


class Episode(Document, SlugMixin, OldIdMixin):
    """
    Represents an Episode. Can only be part of a Podcast
    """

    __metaclass__ = DocumentABCMeta

    title = StringProperty()
    guid = StringProperty()
    description = StringProperty(default="")
    content = StringProperty(default="")
    link = StringProperty()
    released = DateTimeProperty()
    author = StringProperty()
    duration = IntegerProperty()
    filesize = IntegerProperty()
    language = StringProperty()
    last_update = DateTimeProperty()
    outdated = BooleanProperty(default=False)
    mimetypes = StringListProperty()
    merged_ids = StringListProperty()
    urls = StringListProperty()
    podcast = StringProperty(required=True)
    listeners = IntegerProperty()
    content_types = StringListProperty()


    @classmethod
    def get(cls, id, current_id=False):
        r = cls.view('episodes/by_id',
                key=id,
                include_docs=True,
            )

        if not r:
            return None

        obj = r.one()
        if current_id and obj._id != id:
            raise MergedIdException(obj, obj._id)

        return obj


    @classmethod
    def get_multi(cls, ids):
        return cls.view('episodes/by_id',
                include_docs=True,
                keys=ids
            )


    @classmethod
    def for_oldid(self, oldid):
        oldid = int(oldid)
        r = Episode.view('episodes/by_oldid', key=oldid, limit=1, include_docs=True)
        return r.one() if r else None


    @classmethod
    def for_slug(cls, podcast_id, slug):
        r = cls.view('episodes/by_slug',
                key          = [podcast_id, slug],
                include_docs = True
            )
        return r.first() if r else None


    @classmethod
    def for_podcast_url(cls, podcast_url, episode_url, create=False):
        podcast = Podcast.for_url(podcast_url, create=create)

        if not podcast: # podcast does not exist and should not be created
            return None

        return cls.for_podcast_id_url(podcast.get_id(), episode_url, create)


    @classmethod
    def for_podcast_id_url(cls, podcast_id, episode_url, create=False):
        r = cls.view('episodes/by_podcast_url',
                key          = [podcast_id, episode_url],
                include_docs = True,
                reduce       = False,
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
            podcast = Podcast.for_slug_id(p_slug_id)

            if podcast is None:
                return None

            p_id = podcast.get_id()

        return cls.for_slug(p_id, e_slug_id)


    def get_user_state(self, user):
        from mygpo.users.models import EpisodeUserState
        return EpisodeUserState.for_user_episode(user, self)


    def get_all_states(self):
        from mygpo.users.models import EpisodeUserState
        r =  EpisodeUserState.view('episode_states/by_podcast_episode',
            startkey = [self.podcast, self._id, None],
            endkey   = [self.podcast, self._id, {}],
            include_docs=True)
        return iter(r)


    @property
    def url(self):
        return self.urls[0]

    def __repr__(self):
        return 'Episode %s' % self._id


    def listener_count(self, start=None, end={}):
        """ returns the number of users that have listened to this episode """

        from mygpo.users.models import EpisodeUserState
        r = EpisodeUserState.view('listeners/by_episode',
                startkey    = [self._id, start],
                endkey      = [self._id, end],
                reduce      = True,
                group       = True,
                group_level = 2
            )
        return r.first()['value'] if r else 0


    def listener_count_timespan(self, start=None, end={}):
        """ returns (date, listener-count) tuples for all days w/ listeners """

        if isinstance(start, datetime):
            start = start.isoformat()

        if isinstance(end, datetime):
            end = end.isoformat()

        from mygpo.users.models import EpisodeUserState
        r = EpisodeUserState.view('listeners/by_episode',
                startkey    = [self._id, start],
                endkey      = [self._id, end],
                reduce      = True,
                group       = True,
                group_level = 3,
            )

        for res in r:
            date = parser.parse(res['key'][1]).date()
            listeners = res['value']
            yield (date, listeners)


    def get_short_title(self, common_title):
        if not self.title or not common_title:
            return None

        title = self.title.replace(common_title, '').strip()
        title = re.sub(r'^[\W\d]+', '', title)
        return title


    def get_episode_number(self, common_title):
        if not self.title or not common_title:
            return None

        title = self.title.replace(common_title, '').strip()
        match = re.search(r'^\W*(\d+)', title)
        if not match:
            return None

        return int(match.group(1))


    def get_ids(self):
        return set([self._id] + self.merged_ids)


    @classmethod
    @cache_result(timeout=60*60)
    def count(cls):
        r = cls.view('episodes/by_podcast',
                reduce = True,
                stale  = 'update_after',
            )
        return r.one()['value'] if r else 0


    @classmethod
    def all(cls):
        return utils.multi_request_view(cls, 'episodes/by_podcast',
                reduce       = False,
                include_docs = True,
                stale        = 'update_after',
            )

    def __eq__(self, other):
        if other == None:
            return False
        return self._id == other._id


    def __hash__(self):
        return hash(self._id)


    def __str__(self):
        return '<{cls} {title} ({id})>'.format(cls=self.__class__.__name__,
                title=self.title, id=self._id)

    __repr__ = __str__


class SubscriberData(DocumentSchema):
    timestamp = DateTimeProperty()
    subscriber_count = IntegerProperty()

    def __eq__(self, other):
        if not isinstance(other, SubscriberData):
            return False

        return (self.timestamp == other.timestamp) and \
               (self.subscriber_count == other.subscriber_count)

    def __hash__(self):
        return hash(frozenset([self.timestamp, self.subscriber_count]))


class PodcastSubscriberData(Document):
    podcast = StringProperty()
    subscribers = SchemaListProperty(SubscriberData)

    @classmethod
    def for_podcast(cls, id):
        r = cls.view('podcasts/subscriber_data', key=id, include_docs=True)
        if r:
            return r.first()

        data = PodcastSubscriberData()
        data.podcast = id
        return data

    def __repr__(self):
        return 'PodcastSubscriberData for Podcast %s (%s)' % (self.podcast, self._id)


class Podcast(Document, SlugMixin, OldIdMixin):

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
    group = StringProperty()
    group_member_name = StringProperty()
    related_podcasts = StringListProperty()
    subscribers = SchemaListProperty(SubscriberData)
    language = StringProperty()
    content_types = StringListProperty()
    tags = DictProperty()
    restrictions = StringListProperty()
    common_episode_title = StringProperty()
    new_location = StringProperty()
    latest_episode_timestamp = DateTimeProperty()
    episode_count = IntegerProperty()
    random_key = FloatProperty(default=random)


    @classmethod
    def get(cls, id, current_id=False):
        r = cls.view('podcasts/by_id',
                key=id,
                classes=[Podcast, PodcastGroup],
                include_docs=True,
            )

        if not r:
            return None

        podcast_group = r.first()
        return podcast_group.get_podcast_by_id(id, current_id)


    @classmethod
    def for_slug(cls, slug):
        r = cls.view('podcasts/by_slug',
                startkey     = [slug, None],
                endkey       = [slug, {}],
                include_docs = True,
                wrap_doc     = False,
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
        r = cls.view('podcasts/by_id',
                keys         = ids,
                include_docs = True,
                wrap_doc     = False
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
        oldid = int(oldid)
        r = cls.view('podcasts/by_oldid',
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
        r = cls.view('podcasts/by_url',
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


    @classmethod
    def random(cls, language='', chunk_size=5):
        """ Returns an iterator of random podcasts

        optionaly a language code can be specified. If given the podcasts will
        be restricted to this language. chunk_size determines how many podcasts
        will be fetched at once """

        while True:
            rnd = random()
            res = cls.view('podcasts/random',
                    startkey     = [language, rnd],
                    include_docs = True,
                    limit        = chunk_size,
                    stale        = 'ok',
                    wrap_doc     = False,
                )

            if not res:
                break

            for r in res:
                obj = r['doc']
                if obj['doc_type'] == 'Podcast':
                    yield Podcast.wrap(obj)

                elif obj['doc_type'] == 'PodcastGroup':
                    yield PodcastGroup.wrap(obj)


    @classmethod
    def by_last_update(cls):
        res = cls.view('podcasts/by_last_update',
                include_docs = True,
                stale        = 'update_after',
                wrap_doc     = False,
            )

        for r in res:
            obj = r['doc']
            if obj['doc_type'] == 'Podcast':
                yield Podcast.wrap(obj)

            else:
                pid = r[u'key'][1]
                pg = PodcastGroup.wrap(obj)
                podcast = pg.get_podcast_by_id(pid)
                yield podcast


    @classmethod
    def for_language(cls, language, **kwargs):

        res = cls.view('podcasts/by_language',
                startkey     = [language, None],
                endkey       = [language, {}],
                include_docs = True,
                reduce       = False,
                stale        = 'update_after',
                wrap_doc     = False,
                **kwargs
            )

        for r in res:
            obj = r['doc']
            if obj['doc_type'] == 'Podcast':
                yield Podcast.wrap(obj)

            else:
                pid = r[u'key'][1]
                pg = PodcastGroup.wrap(obj)
                podcast = pg.get_podcast_by_id(pid)
                yield podcast


    @classmethod
    @cache_result(timeout=60*60)
    def count(cls):
        # TODO: fix number calculation
        r = cls.view('podcasts/by_id',
                limit = 0,
                stale = 'update_after',
            )
        return r.total_rows


    def get_podcast_by_id(self, id, current_id=False):
        if current_id and id != self.get_id():
            raise MergedIdException(self, self.get_id())

        return self


    get_podcast_by_oldid = get_podcast_by_id
    get_podcast_by_url = get_podcast_by_id


    def get_id(self):
        return self.id or self._id

    def get_ids(self):
        return set([self.get_id()] + self.merged_ids)

    @property
    def display_title(self):
        return self.title or self.url


    def group_with(self, other, grouptitle, myname, othername):

        if self.group and (self.group == other.group):
            # they are already grouped
            return

        group1 = PodcastGroup.get(self.group) if self.group else None
        group2 = PodcastGroup.get(other.group) if other.group else None

        if group1 and group2:
            raise ValueError('both podcasts already are in different groups')

        elif not (group1 or group2):
            group = PodcastGroup(title=grouptitle)
            group.save()
            group.add_podcast(self, myname)
            group.add_podcast(other, othername)
            return group

        elif group1:
            group1.add_podcast(other, othername)
            return group1

        else:
            group2.add_podcast(self, myname)
            return group2



    def get_episodes(self, since=None, until={}, **kwargs):

        if kwargs.get('descending', False):
            since, until = until, since

        if isinstance(since, datetime):
            since = since.isoformat()

        if isinstance(until, datetime):
            until = until.isoformat()

        res = Episode.view('episodes/by_podcast',
                startkey     = [self.get_id(), since],
                endkey       = [self.get_id(), until],
                include_docs = True,
                reduce       = False,
                **kwargs
            )

        return iter(res)


    def get_episode_count(self, since=None, until={}, **kwargs):

        # use stored episode count for better performance
        if getattr(self, 'episode_count', None) is not None:
            return self.episode_count

        if kwargs.get('descending', False):
            since, until = until, since

        if isinstance(since, datetime):
            since = since.isoformat()

        if isinstance(until, datetime):
            until = until.isoformat()

        res = Episode.view('episodes/by_podcast',
                startkey     = [self.get_id(), since],
                endkey       = [self.get_id(), until],
                reduce       = True,
                group_level  = 1,
                **kwargs
            )

        return res.one()['value']


    def get_common_episode_title(self, num_episodes=100):

        if self.common_episode_title:
            return self.common_episode_title

        episodes = self.get_episodes(descending=True, limit=num_episodes)

        # We take all non-empty titles
        titles = filter(None, (e.title for e in episodes))
        # get the longest common substring
        common_title = utils.longest_substr(titles)

        # but consider only the part up to the first number. Otherwise we risk
        # removing part of the number (eg if a feed contains episodes 100-199)
        common_title = re.search(r'^\D*', common_title).group(0)

        if len(common_title.strip()) < 2:
            return None

        return common_title


    @cache_result(timeout=60*60)
    def get_latest_episode(self):
        # since = 1 ==> has a timestamp
        episodes = self.get_episodes(since=1, descending=True, limit=1)
        return next(episodes, None)


    def get_episode_before(self, episode):
        if not episode.released:
            return None

        prevs = self.get_episodes(until=episode.released, descending=True,
                limit=1)

        try:
            return next(prevs)
        except StopIteration:
            return None


    def get_episode_after(self, episode):
        if not episode.released:
            return None

        nexts = self.get_episodes(since=episode.released, limit=1)

        try:
            return next(nexts)
        except StopIteration:
            return None


    def get_episode_for_slug(self, slug):
        return Episode.for_slug(self.get_id(), slug)


    @property
    def url(self):
        return self.urls[0]


    def get_podcast(self):
        return self


    def get_logo_url(self, size):
        if self.logo_url:
            filename = hashlib.sha1(self.logo_url).hexdigest()
        else:
            filename = 'podcast-%d.png' % (hash(self.title) % 5, )

        prefix = CoverArt.get_prefix(filename)

        return reverse('logo', args=[size, prefix, filename])


    def subscriber_change(self):
        prev = self.prev_subscriber_count()
        if prev <= 0:
            return 0

        return self.subscriber_count() / prev


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
        return PodcastUserState.view('podcast_states/by_podcast',
            startkey = [self.get_id(), None],
            endkey   = [self.get_id(), {}],
            include_docs=True)

    def get_all_subscriber_data(self):
        subdata = PodcastSubscriberData.for_podcast(self.get_id())
        return sorted(self.subscribers + subdata.subscribers,
                key=lambda s: s.timestamp)


    @repeat_on_conflict()
    def subscribe(self, user, device):
        state = self.get_user_state(user)
        state.subscribe(device)
        try:
            state.save()
        except Unauthorized as ex:
            raise SubscriptionException(ex)


    @repeat_on_conflict()
    def unsubscribe(self, user, device):
        state = self.get_user_state(user)
        state.unsubscribe(device)
        try:
            state.save()
        except Unauthorized as ex:
            raise SubscriptionException(ex)


    def subscribe_targets(self, user):
        """
        returns all Devices and SyncGroups on which this podcast can be subsrbied. This excludes all
        devices/syncgroups on which the podcast is already subscribed
        """
        targets = []

        subscriptions_by_devices = user.get_subscriptions_by_device()

        for group in user.get_grouped_devices():

            if group.is_synced:

                dev = group.devices[0]

                if not self.get_id() in subscriptions_by_devices[dev.id]:
                    targets.append(group.devices)

            else:
                for device in group.devices:
                    if not self.get_id() in subscriptions_by_devices[device.id]:
                        targets.append(device)

        return targets


    def listener_count(self):
        """ returns the number of users that have listened to this podcast """

        from mygpo.users.models import EpisodeUserState
        r = EpisodeUserState.view('listeners/by_podcast',
                startkey    = [self.get_id(), None],
                endkey      = [self.get_id(), {}],
                group       = True,
                group_level = 1,
                reduce      = True,
            )
        return r.first()['value'] if r else 0


    def listener_count_timespan(self, start=None, end={}):
        """ returns (date, listener-count) tuples for all days w/ listeners """

        if isinstance(start, datetime):
            start = start.isoformat()

        if isinstance(end, datetime):
            end = end.isoformat()

        from mygpo.users.models import EpisodeUserState
        r = EpisodeUserState.view('listeners/by_podcast',
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
        r = EpisodeUserState.view('listeners/by_podcast_episode',
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


    def get_episode_states(self, user_id):
        """ Returns the latest episode actions for the podcast's episodes """

        from mygpo.users.models import EpisodeUserState
        db = get_main_database()

        res = db.view('episode_states/by_user_podcast',
                startkey = [user_id, self.get_id(), None],
                endkey   = [user_id, self.get_id(), {}],
            )

        for r in res:
            action = r['value']
            yield action


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
        return cls.view('podcasts/podcasts_groups', include_docs=True,
            classes=[Podcast, PodcastGroup]).iterator()


    def __eq__(self, other):
        if not self.get_id():
            return self == other

        if other == None:
            return False

        return self.get_id() == other.get_id()


    @classmethod
    def all_podcasts(cls):
        res = utils.multi_request_view(cls, 'podcasts/by_id',
                wrap         = False,
                include_docs = True,
                stale        = 'update_after',
            )

        for r in res:
            obj = r['doc']
            if obj['doc_type'] == 'Podcast':
                yield Podcast.wrap(obj)
            else:
                pid = r[u'key']
                pg = PodcastGroup.wrap(obj)
                podcast = pg.get_podcast_by_id(pid)
                yield podcast



class PodcastGroup(Document, SlugMixin, OldIdMixin):
    title    = StringProperty()
    podcasts = SchemaListProperty(Podcast)

    def get_id(self):
        return self._id

    @classmethod
    def for_oldid(cls, oldid):
        oldid = int(oldid)
        r = cls.view('podcasts/groups_by_oldid', \
            key=oldid, limit=1, include_docs=True)
        return r.first() if r else None


    @classmethod
    def for_slug_id(cls, slug_id):
        """ Returns the Podcast for either an CouchDB-ID for a Slug """

        if utils.is_couchdb_id(slug_id):
            return cls.get(slug_id)
        else:
            #TODO: implement
            return cls.for_slug(slug_id)


    def get_podcast_by_id(self, id, current_id=False):
        for podcast in self.podcasts:
            if podcast.get_id() == id:
                return podcast

            if id in podcast.merged_ids:
                if current_id:
                    raise MergedIdException(podcast, podcast.get_id())

                return podcast


    def get_podcast_by_oldid(self, oldid):
        for podcast in list(self.podcasts):
            if podcast.oldid == oldid:
                return podcast


    def get_podcast_by_url(self, url):
        for podcast in self.podcasts:
            if url in list(podcast.urls):
                return podcast


    def subscriber_change(self):
        prev = self.prev_subscriber_count()
        if not prev:
            return 0

        return self.subscriber_count() / prev


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
            filename = hashlib.sha1(self.logo_url).hexdigest()
        else:
            filename = 'podcast-%d.png' % (hash(self.title) % 5, )

        prefix = CoverArt.get_prefix(filename)

        return reverse('logo', args=[size, prefix, filename])


    def add_podcast(self, podcast, member_name):

        if not self._id:
            raise ValueError('group has to have an _id first')

        if not podcast._id:
            raise ValueError('podcast needs to have an _id first')

        if not podcast.id:
            podcast.id = podcast._id

        podcast.delete()
        podcast.group = self._id
        podcast.group_member_name = member_name
        self.podcasts = sorted(self.podcasts + [podcast],
                        key=Podcast.subscriber_count, reverse=True)
        self.save()


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
        r = cls.view('sanitizing_rules/by_target', include_docs=True,
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
        r = cls.view('sanitizing_rules/by_slug', include_docs=True,
            key=slug)
        return r.one() if r else None


    def __repr__(self):
        return 'SanitizingRule %s' % self._id
