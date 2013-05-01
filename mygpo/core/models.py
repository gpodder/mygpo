from __future__ import division

import hashlib
import re
from random import random

from couchdbkit.ext.django.schema import *
from restkit.errors import Unauthorized

from django.core.urlresolvers import reverse

from mygpo.decorators import repeat_on_conflict
from mygpo import utils
from mygpo.cache import cache_result
from mygpo.core.proxy import DocumentABCMeta
from mygpo.core.slugs import SlugMixin
from mygpo.core.oldid import OldIdMixin
from mygpo.web.logo import CoverArt

# make sure this code is executed at startup
from mygpo.core.signals import *


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
    flattr_url = StringProperty()
    created_timestamp = IntegerProperty()



    @property
    def url(self):
        return self.urls[0]

    def __repr__(self):
        return 'Episode %s' % self._id



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


    @property
    def needs_update(self):
        """ Indicates if the object requires an updated from its feed """
        return not self.title and not self.outdated


    def __eq__(self, other):
        if other is None:
            return False
        return self._id == other._id


    def __hash__(self):
        return hash(self._id)


    def __unicode__(self):
        return u'<{cls} {title} ({id})>'.format(cls=self.__class__.__name__,
                title=self.title, id=self._id)



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
    flattr_url = StringProperty()
    outdated = BooleanProperty(default=False)
    created_timestamp = IntegerProperty()
    hub = StringProperty()



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



    def get_common_episode_title(self, num_episodes=100):

        if self.common_episode_title:
            return self.common_episode_title

        from mygpo.db.couchdb.episode import episodes_for_podcast
        episodes = episodes_for_podcast(self, descending=True, limit=num_episodes)

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


    def get_episode_before(self, episode):
        if not episode.released:
            return None

        from mygpo.db.couchdb.episode import episodes_for_podcast
        prevs = episodes_for_podcast(self, until=episode.released,
                descending=True, limit=1)

        return next(iter(prevs), None)


    def get_episode_after(self, episode):
        if not episode.released:
            return None

        from mygpo.db.couchdb.episode import episodes_for_podcast
        from datetime import timedelta
        nexts = episodes_for_podcast(self,
                since=episode.released + timedelta(seconds=1), limit=1)

        return next(iter(nexts), None)


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



    @repeat_on_conflict()
    def subscribe(self, user, device):
        from mygpo.db.couchdb.podcast_state import podcast_state_for_user_podcast
        state = podcast_state_for_user_podcast(user, self)
        state.subscribe(device)
        try:
            state.save()
            subscription_changed.send(sender=self, user=user, device=device,
                                      subscribed=True)
        except Unauthorized as ex:
            raise SubscriptionException(ex)


    @repeat_on_conflict()
    def unsubscribe(self, user, device):
        from mygpo.db.couchdb.podcast_state import podcast_state_for_user_podcast
        state = podcast_state_for_user_podcast(user, self)
        state.unsubscribe(device)
        try:
            state.save()
            subscription_changed.send(sender=self, user=user, device=device,
                                      subscribed=False)
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


    @property
    def needs_update(self):
        """ Indicates if the object requires an updated from its feed """
        return not self.title and not self.outdated


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
        if group:  # we are part of a PodcastGroup
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


    def __eq__(self, other):
        if not self.get_id():
            return self == other

        if other is None:
            return False

        return self.get_id() == other.get_id()



class PodcastGroup(Document, SlugMixin, OldIdMixin):
    title    = StringProperty()
    podcasts = SchemaListProperty(Podcast)

    def get_id(self):
        return self._id


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


    @property
    def needs_update(self):
        """ Indicates if the object requires an updated from its feed """
        # A PodcastGroup has been manually created and therefore never
        # requires an update
        return False

    def get_podcast(self):
        # return podcast with most subscribers (bug 1390)
        return sorted(self.podcasts, key=Podcast.subscriber_count,
                reverse=True)[0]


    @property
    def logo_url(self):
        return utils.first(p.logo_url for p in self.podcasts)

    @logo_url.setter
    def logo_url(self, value):
        self.podcasts[0].logo_url = value


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



class SanitizingRule(Document):
    slug        = StringProperty()
    applies_to  = StringListProperty()
    search      = StringProperty()
    replace     = StringProperty()
    priority    = IntegerProperty()
    description = StringProperty()


    def __repr__(self):
        return 'SanitizingRule %s' % self._id
