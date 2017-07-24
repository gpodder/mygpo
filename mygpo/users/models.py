

import re
import uuid
import collections
import dateutil.parser

from django.core.validators import RegexValidator
from django.db import transaction, models
from django.db.models import Q
from django.contrib.auth.models import User as DjangoUser
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.conf import settings

from mygpo.core.models import (TwitterModel, UUIDModel,
    GenericManager, DeleteableModel, )
from mygpo.usersettings.models import UserSettings
from mygpo.podcasts.models import Podcast, Episode
from mygpo.utils import random_token

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
            raise UserProxy.DoesNotExist


class UserProxyManager(GenericManager):
    """ Manager for the UserProxy model """

    def get_queryset(self):
        return UserProxyQuerySet(self.model, using=self._db)

    def from_user(self, user):
        """ Get the UserProxy corresponding for the given User """
        return self.get(pk=user.pk)


class UserProxy(DjangoUser):

    objects = UserProxyManager()

    # only accept ASCII usernames, see
    # https://docs.djangoproject.com/en/dev/releases/1.10/#official-support-for-unicode-usernames
    username_validator = ASCIIUsernameValidator()

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


class UserProfile(TwitterModel):
    """ Additional information stored for a User """

    # the user to which this profile belongs
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='profile')

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

    def create_new_token(self, token_name):
        """ resets a token """

        if token_name not in TOKEN_NAMES:
            raise TokenException('Invalid token name %s' % token_name)

        setattr(self, token_name, random_token())

    @property
    def settings(self):
        try:
            return UserSettings.objects.get(user=self.user, content_type=None)
        except UserSettings.DoesNotExist:
            return UserSettings(user=self.user, content_type=None,
                                object_id=None)


class SyncGroup(models.Model):
    """ A group of Clients """

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    def sync(self):
        """ Sync the group, ie bring all members up-to-date """
        from mygpo.subscriptions import subscribe

        # get all subscribed podcasts
        podcasts = set(self.get_subscribed_podcasts())

        # bring each client up to date, it it is subscribed to all podcasts
        for client in self.client_set.all():
            missing_podcasts = self.get_missing_podcasts(client, podcasts)
            for podcast in missing_podcasts:
                subscribe(podcast, self.user, client)

    def get_subscribed_podcasts(self):
        return Podcast.objects.filter(subscription__client__sync_group=self)

    def get_missing_podcasts(self, client, all_podcasts):
        """ the podcasts required to bring the device to the group's state """
        client_podcasts = set(client.get_subscribed_podcasts())
        return all_podcasts.difference(client_podcasts)

    @property
    def display_name(self):
        clients = self.client_set.all()
        return ', '.join(client.display_name for client in clients)


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

    sync_group = models.ForeignKey(SyncGroup, null=True, blank=True,
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
            other.sync_group = self.sync_group
            other.save()

        elif other.sync_group is not None:
            self.sync_group = other.sync_group
            self.save()

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

            if self in group.devices and group.is_synced:
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

    @property
    def display_name(self):
        return self.name or self.uid

    def __str__(self):
        return '{name} ({uid})'.format(name=self.name, uid=self.uid)


TOKEN_NAMES = ('subscriptions_token', 'favorite_feeds_token',
        'publisher_update_token', 'userpage_token')


class TokenException(Exception):
    pass


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
