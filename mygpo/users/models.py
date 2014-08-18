from __future__ import unicode_literals

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

from mygpo.core.models import (TwitterModel, UUIDModel, SettingsModel,
    GenericManager, DeleteableModel, )
from mygpo.podcasts.models import Podcast, Episode
from mygpo.utils import random_token
from mygpo.core.proxy import DocumentABCMeta, proxy_object
from mygpo.decorators import repeat_on_conflict
from mygpo.users.ratings import RatingMixin
from mygpo.users.subscriptions import subscription_changes
from mygpo.users.settings import FAV_FLAG, PUBLIC_SUB_PODCAST, SettingsMixin
from mygpo.db.couchdb.user import user_history, device_history

import logging
logger = logging.getLogger(__name__)


RE_DEVICE_UID = re.compile(r'^[\w.-]+$')

# TODO: derive from ValidationException?
class InvalidEpisodeActionAttributes(ValueError):
    """ raised when the attribues of an episode action fail validation """


class SubscriptionException(Exception):
    """ raised when a subscription can not be modified """


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
        from mygpo.subscriptions import get_subscribed_podcasts
        User = get_user_model()
        user = User.objects.get(profile__uuid=self.user)
        subscriptions = [sp.podcast.id.hex for sp in
                         get_subscribed_podcasts(user)]

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

        # get all subscribed podcasts
        podcasts = set(self.get_subscribed_podcasts())

        # bring each client up to date, it it is subscribed to all podcasts
        for client in self.client_set.all():
            missing_podcasts = self.get_missing_podcasts(client, podcasts)
            for podcast in missing_podcasts:
                subscribe(podcast, self.user, client)

    def get_subscribed_podcasts(self):
        return Podcast.objects.filter(subscription__device__sync_group=self)

    def get_missing_podcasts(self, client, all_podcasts):
        """ the podcasts required to bring the device to the group's state """
        client_podcasts = set(client.get_subscribed_podcasts())
        return all_podcasts.difference(client_podcasts)


class Client(UUIDModel, DeleteableModel):
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

    def get_subscribed_podcasts(self):
        """ Returns all subscribed podcasts for the device

        The attribute "url" contains the URL that was used when subscribing to
        the podcast """
        return Podcast.objects.filter(subscription__client=self)

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


TOKEN_NAMES = ('subscriptions_token', 'favorite_feeds_token',
        'publisher_update_token', 'userpage_token')


class TokenException(Exception):
    pass


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
