import re
import uuid
import collections
from datetime import datetime
import dateutil.parser
from itertools import imap
import random
import string

from couchdbkit.ext.django.schema import *
from uuidfield import UUIDField

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import transaction, models
from django.db.models import Q
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.cache import cache
from django.contrib import messages

from django_couchdb_utils.registration.models import User as BaseUser

from mygpo.core.models import (TwitterModel, UUIDModel, SettingsModel,
    GenericManager, )
from mygpo.podcasts.models import Podcast, Episode
from mygpo.utils import random_token
from mygpo.core.proxy import DocumentABCMeta, proxy_object
from mygpo.decorators import repeat_on_conflict
from mygpo.users.ratings import RatingMixin
from mygpo.users.subscriptions import (subscription_changes,
    podcasts_for_states, get_subscribed_podcast_ids)
from mygpo.users.settings import FAV_FLAG, PUBLIC_SUB_PODCAST, SettingsMixin
from mygpo.db.couchdb.user import user_history, device_history

# make sure this code is executed at startup
from mygpo.users.signals import *

import logging
logger = logging.getLogger(__name__)


RE_DEVICE_UID = re.compile(r'^[\w.-]+$')

# TODO: derive from ValidationException?
class InvalidEpisodeActionAttributes(ValueError):
    """ raised when the attribues of an episode action fail validation """


class SubscriptionException(Exception):
    """ raised when a subscription can not be modified """


class DeviceDoesNotExist(Exception):
    pass


class DeviceDeletedException(DeviceDoesNotExist):
    pass


GroupedDevices = collections.namedtuple('GroupedDevices', 'is_synced devices')


class UIDValidator(RegexValidator):
    """ Validates that the Device UID conforms to the given regex """
    regex = RE_DEVICE_UID
    message = 'Invalid Device ID'
    code='invalid-uid'


class UserProxyQuerySet(models.QuerySet):

    def by_username_or_email(self, username, email):
        """ Queries for a User by username or email """
        q = Q()

        if username:
            q |= Q(username=username)

        elif email:
            q |= Q(email=email)

        if q:
            return self.get(q)
        else:
            return self.none()


class UserProxyManager(GenericManager):
    """ Manager for the UserProxy model """

    def get_queryset(self):
        return UserProxyQuerySet(self.model, using=self._db)

    def from_user(self, user):
        """ Get the UserProxy corresponding for the given User """
        return self.get(pk=user.pk)


class UserProxy(DjangoUser):

    objects = UserProxyManager()

    class Meta:
        proxy = True

    @transaction.atomic
    def activate(self):
        self.is_active = True
        self.save()

        self.profile.activation_key = None
        self.profile.save()


    def get_grouped_devices(self):
        """ Returns groups of synced devices and a unsynced group """

        clients = Client.objects.filter(user=self, deleted=False)\
                                .order_by('-sync_group')

        last_group = object()
        group = None

        for client in clients:
            # check if we have just found a new group
            if last_group != client.sync_group:
                if group != None:
                    yield group

                group = GroupedDevices(client.sync_group is not None, [])

            last_group = client.sync_group
            group.devices.append(client)

        # yield remaining group
        if group != None:
            yield group


class UserProfile(TwitterModel, SettingsModel):
    """ Additional information stored for a User """

    # the user to which this profile belongs
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='profile')

    # the CouchDB _id of the user
    uuid = UUIDField(unique=True)

    # if False, suggestions should be updated
    suggestions_up_to_date = models.BooleanField(default=False)

    # text the user entered about himeself
    about = models.TextField(blank=True)

    # Google email address for OAuth login
    google_email = models.CharField(max_length=100, null=True)

    # token for accessing subscriptions of this use
    subscriptions_token = models.CharField(max_length=32, null=True,
                                           default=random_token)

    # token for accessing the favorite-episodes feed of this user
    favorite_feeds_token = models.CharField(max_length=32, null=True,
                                            default=random_token)

    # token for automatically updating feeds published by this user
    publisher_update_token = models.CharField(max_length=32, null=True,
                                              default=random_token)

    # token for accessing the userpage of this user
    userpage_token = models.CharField(max_length=32, null=True,
                                      default=random_token)

    # key for activating the user
    activation_key = models.CharField(max_length=40, null=True)

    def get_token(self, token_name):
        """ returns a token """

        if token_name not in TOKEN_NAMES:
            raise TokenException('Invalid token name %s' % token_name)

        return getattr(self, token_name)


class Suggestions(Document, RatingMixin):
    user = StringProperty(required=True)
    user_oldid = IntegerProperty()
    podcasts = StringListProperty()
    blacklist = StringListProperty()


    def get_podcasts(self, count=None):
        User = get_user_model()
        user = User.objects.get(profile__uuid=self.user)
        # TODO: re-include later on
        #subscriptions = get_subscribed_podcast_ids(user)
        subscriptions = []

        ids = filter(lambda x: not x in self.blacklist + subscriptions, self.podcasts)
        if count:
            ids = ids[:count]

        podcasts = Podcast.objects.filter(id__in=ids).prefetch_related('slugs')
        return filter(lambda x: x and x.title, podcasts)


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

    # walltime of the event (assigned by the uploading client, defaults to now)
    timestamp     = DateTimeProperty(required=True, default=datetime.utcnow)

    # upload time of the event
    upload_timestamp = IntegerProperty(required=True)

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
           ((self.total is None) or (self.started is None)):
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



    def add_actions(self, actions):
        map(EpisodeAction.validate_time_values, actions)
        self.actions = list(self.actions) + actions
        self.actions = list(set(self.actions))
        self.actions = sorted(self.actions, key=lambda x: x.timestamp)


    def is_favorite(self):
        return self.get_wksetting(FAV_FLAG)


    def set_favorite(self, set_to=True):
        self.settings[FAV_FLAG.name] = set_to


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


    def remove_device(self, device):
        """
        Removes all actions from the podcast state that refer to the
        given device
        """
        self.actions = filter(lambda a: a.device != device.id, self.actions)


    def subscribe(self, device):
        action = SubscriptionAction()
        action.action = 'subscribe'
        action.device = device.id.hex
        self.add_actions([action])


    def unsubscribe(self, device):
        action = SubscriptionAction()
        action.action = 'unsubscribe'
        action.device = device.id.hex
        self.add_actions([action])


    def add_actions(self, actions):
        self.actions = list(set(self.actions + actions))
        self.actions = sorted(self.actions)


    def add_tags(self, tags):
        self.tags = list(set(self.tags + tags))


    def set_device_state(self, devices):
        disabled_devices = [device.id for device in devices if device.deleted]
        #self.disabled_devices = disabled_devices


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


    def is_subscribed_on(self, device):
        """ checks if the podcast is subscribed on the given device """

        for action in reversed(self.actions):
            if not action.device == device.id.hex:
                continue

            # we only need to check the latest action for the device
            return (action.action == 'subscribe')

        # we haven't found any matching action
        return False


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


class SyncGroup(models.Model):
    """ A group of Clients """

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    def sync(self):
        """ Sync the group, ie bring all members up-to-date """

        group_state = self.get_group_state()

        for device in SyncGroup.objects.filter(sync_group=self):
            sync_actions = self.get_sync_actions(device, group_state)
            device.apply_sync_actions(sync_actions)

    def get_group_state(self):
        """ Returns the group's subscription state

        The state is represented by the latest actions for each podcast """

        devices = Client.objects.filter(sync_group=self)
        state = {}

        for d in devices:
            actions = dict(d.get_latest_changes())
            for podcast_id, action in actions.items():
                if not podcast_id in state or \
                        action.timestamp > state[podcast_id].timestamp:
                    state[podcast_id] = action

        return state

    def get_sync_actions(self, device, group_state):
        """ Get the actions required to bring the device to the group's state

        After applying the actions the device reflects the group's state """

        # Filter those that describe actual changes to the current state
        add, rem = [], []
        current_state = dict(device.get_latest_changes())

        for podcast_id, action in group_state.items():

            # Sync-Actions must be newer than current state
            if podcast_id in current_state and \
               action.timestamp <= current_state[podcast_id].timestamp:
                continue

            # subscribe only what hasn't been subscribed before
            if action.action == 'subscribe' and \
                        (podcast_id not in current_state or \
                         current_state[podcast_id].action == 'unsubscribe'):
                add.append(podcast_id)

            # unsubscribe only what has been subscribed before
            elif action.action == 'unsubscribe' and \
                        podcast_id in current_state and \
                        current_state[podcast_id].action == 'subscribe':
                rem.append(podcast_id)

        return add, rem



class Client(UUIDModel):
    """ A client application """

    DESKTOP = 'desktop'
    LAPTOP = 'laptop'
    MOBILE = 'mobile'
    SERVER = 'server'
    TABLET = 'tablet'
    OTHER = 'other'

    TYPES = (
        (DESKTOP, _('Desktop')),
        (LAPTOP, _('Laptop')),
        (MOBILE, _('Cell phone')),
        (SERVER, _('Server')),
        (TABLET, _('Tablet')),
        (OTHER, _('Other')),
    )

    # User-assigned ID; must be unique for the user
    uid = models.CharField(max_length=64, validators=[UIDValidator()])

    # the user to which the Client belongs
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    # User-assigned name
    name = models.CharField(max_length=100, default='New Device')

    # one of several predefined types
    type = models.CharField(max_length=max(len(k) for k, v in TYPES),
                            choices=TYPES, default=OTHER)

    # indicates if the user has deleted the client
    deleted = models.BooleanField(default=False)

    # user-agent string from which the Client was last accessed (for writing)
    user_agent = models.CharField(max_length=300, null=True, blank=True)

    sync_group = models.ForeignKey(SyncGroup, null=True,
                                   on_delete=models.PROTECT)

    class Meta:
        unique_together = (
            ('user', 'uid'),
        )

    @transaction.atomic
    def sync_with(self, other):
        """ Puts two devices in a common sync group"""

        if self.user != other.user:
            raise ValueError('the devices do not belong to the user')

        if self.sync_group is not None and \
           other.sync_group is not None and \
           self.sync_group != other.sync_group:
            # merge sync_groups
            ogroup = other.sync_group
            Client.objects.filter(sync_group=ogroup)\
                          .update(sync_group=self.sync_group)
            ogroup.delete()

        elif self.sync_group is None and \
             other.sync_group is None:
            sg = SyncGroup.objects.create(user=self.user)
            other.sync_group = sg
            other.save()
            self.sync_group = sg
            self.save()

        elif self.sync_group is not None:
            self.sync_group = other.sync_group
            self.save()

        elif other.sync_group is not None:
            other.sync_group = self.sync_group
            other.save()

    def stop_sync(self):
        """ Stop synchronisation with other clients """
        sg = self.sync_group

        logger.info('Stopping synchronisation of %r', self)
        self.sync_group = None
        self.save()

        clients = Client.objects.filter(sync_group=sg)
        logger.info('%d other clients remaining in sync group', len(clients))

        if len(clients) < 2:
            logger.info('Deleting sync group %r', sg)
            for client in clients:
                client.sync_group = None
                client.save()

            sg.delete()

    def get_sync_targets(self):
        """ Returns the devices and groups with which the device can be synced

        Groups are represented as lists of devices """

        sg = self.sync_group

        user = UserProxy.objects.from_user(self.user)
        for group in user.get_grouped_devices():

            if self in group.devices:
                # the device's group can't be a sync-target
                continue

            elif group.is_synced:
                yield group.devices

            else:
                # every unsynced device is a sync-target
                for dev in group.devices:
                    if not dev == self:
                        yield dev

    def apply_sync_actions(self, sync_actions):
        """ Applies the sync-actions to the client """

        from mygpo.db.couchdb.podcast_state import subscribe, unsubscribe
        from mygpo.users.models import SubscriptionException
        add, rem = sync_actions

        podcasts = Podcast.objects.filter(id__in=(add+rem))
        podcasts = {podcast.id: podcast for podcast in podcasts}

        for podcast_id in add:
            podcast = podcasts.get(podcast_id, None)
            if podcast is None:
                continue
            try:
                subscribe(podcast, self.user, self)
            except SubscriptionException as e:
                logger.warn('Web: %(username)s: cannot sync device: %(error)s' %
                    dict(username=self.user.username, error=repr(e)))

        for podcast_id in rem:
            podcast = podcasts.get(podcast_id, None)
            if not podcast:
                continue

            try:
                unsubscribe(podcast, self.user, self)
            except SubscriptionException as e:
                logger.warn('Web: %(username)s: cannot sync device: %(error)s' %
                    dict(username=self.user.username, error=repr(e)))

    def get_subscription_changes(self, since, until):
        """
        Returns the subscription changes for the device as two lists.
        The first lists contains the Ids of the podcasts that have been
        subscribed to, the second list of those that have been unsubscribed
        from.
        """

        from mygpo.db.couchdb.podcast_state import podcast_states_for_device
        podcast_states = podcast_states_for_device(self.id.hex)
        return subscription_changes(self.id.hex, podcast_states, since, until)

    def get_latest_changes(self):
        from mygpo.db.couchdb.podcast_state import podcast_states_for_device
        podcast_states = podcast_states_for_device(self.id.hex)
        for p_state in podcast_states:
            actions = filter(lambda x: x.device == self.id.hex, reversed(p_state.actions))
            if actions:
                yield (p_state.podcast, actions[0])

    def get_subscribed_podcast_ids(self):
        from mygpo.db.couchdb.podcast_state import get_subscribed_podcast_states_by_device
        states = get_subscribed_podcast_states_by_device(self)
        return [state.podcast for state in states]

    def get_subscribed_podcasts(self):
        """ Returns all subscribed podcasts for the device

        The attribute "url" contains the URL that was used when subscribing to
        the podcast """
        from mygpo.db.couchdb.podcast_state import get_subscribed_podcast_states_by_device
        states = get_subscribed_podcast_states_by_device(self)
        return podcasts_for_states(states)

    def synced_with(self):
        if not self.sync_group:
            return []

        return Client.objects.filter(sync_group=self.sync_group)\
                             .exclude(pk=self.pk)

    def __str__(self):
        return '{} ({})'.format(self.name.encode('ascii', errors='replace'),
                                self.uid.encode('ascii', errors='replace'))

    def __unicode__(self):
        return u'{} ({})'.format(self.name, self.uid)


class Device(Document, SettingsMixin):
    id       = StringProperty(default=lambda: uuid.uuid4().hex)
    oldid    = IntegerProperty(required=False)
    uid      = StringProperty(required=True)
    name     = StringProperty(required=True, default='New Device')
    type     = StringProperty(required=True, default='other')
    deleted  = BooleanProperty(default=False)
    user_agent = StringProperty()



    def __hash__(self):
        return hash(frozenset([self.id, self.uid, self.name, self.type, self.deleted]))


    def __eq__(self, other):
        return self.id == other.id


    def __repr__(self):
        return '<{cls} {id}>'.format(cls=self.__class__.__name__, id=self.id)



TOKEN_NAMES = ('subscriptions_token', 'favorite_feeds_token',
        'publisher_update_token', 'userpage_token')


class TokenException(Exception):
    pass


class User(BaseUser, SettingsMixin):
    oldid    = IntegerProperty()
    devices  = SchemaListProperty(Device)
    published_objects = StringListProperty()
    deleted  = BooleanProperty(default=False)
    suggestions_up_to_date = BooleanProperty(default=False)
    twitter = StringProperty()
    about   = StringProperty()
    google_email = StringProperty()

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

    @property
    def active_devices(self):
        not_deleted = lambda d: not d.deleted
        return filter(not_deleted, self.devices)


    @property
    def inactive_devices(self):
        deleted = lambda d: d.deleted
        return filter(deleted, self.devices)


    def get_devices_by_id(self, device_ids=None):
        """ Returns a dict of {devices_id: device} """
        if device_ids is None:
            # return all devices
            devices = self.devices
        else:
            devices = self.get_devices(device_ids)

        return {device.id: device for device in devices}


    def get_device(self, id):

        if not hasattr(self, '__device_by_id'):
            self.__devices_by_id = self.get_devices_by_id()

        return self.__devices_by_id.get(id, None)


    def get_devices(self, ids):
        return filter(None, (self.get_device(dev_id) for dev_id in ids))


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


    def remove_device(self, device):
        devices = list(self.devices)
        ids = [x.id for x in devices]
        if not device.id in ids:
            return

        index = ids.index(device.id)
        devices.pop(index)
        self.devices = devices

        if self.is_synced(device):
            device.stop_sync()

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
            # TODO: max_per_podcast
            new_episodes = podcast.episode_set.filter(release__isnull=False,
                                                      released__lt=max_date)
            new_episodes = new_episodes[:max_per_podcast]
            episodes = sorted(episodes+new_episodes, key=cmp_key, reverse=True)


        # yield the remaining episodes
        for episode in episodes:
            podcast = podcast_dict.get(episode.podcast, None)
            yield proxy_object(episode, podcast=podcast)


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
            podcasts = Podcast.objects.filter(id__in=podcast_ids)\
                                      .prefetch_related('slugs')
            podcasts = {podcast.id.hex: podcast for podcast in podcasts}

        if episodes is None:
            # load episode data
            episode_ids = [getattr(x, 'episode_id', None) for x in entries]
            episode_ids = filter(None, episode_ids)
            episodes = Episode.objects.filter(id__in=episode_ids)\
                                      .select_related('podcast')\
                                      .prefetch_related('slugs',
                                                        'podcast__slugs')
            episodes = {episode.id.hex: episode for episode in episodes}

        # load device data
        # does not need pre-populated data because no db-access is required
        device_ids = [getattr(x, 'device_id', None) for x in entries]
        device_ids = filter(None, device_ids)
        devices = {client.id.hex: client for client in user.client_set.all()}


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


def create_missing_profile(sender, **kwargs):
    """ Creates a UserProfile if a User doesn't have one """
    user = kwargs['instance']

    if not hasattr(user, 'profile'):
        # TODO: remove uuid column once migration from CouchDB is complete
        import uuid
        profile = UserProfile.objects.create(user=user, uuid=uuid.uuid1())
        user.profile = profile
