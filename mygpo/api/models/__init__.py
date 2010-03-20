#
# This file is part of my.gpodder.org.
#
# my.gpodder.org is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# my.gpodder.org is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public
# License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with my.gpodder.org. If not, see <http://www.gnu.org/licenses/>.
#

from django.db import models
from django.contrib.auth.models import User, UserManager
from datetime import datetime
from django.utils.translation import ugettext as _
import hashlib
import re

from mygpo.api.constants import EPISODE_ACTION_TYPES, DEVICE_TYPES, SUBSCRIBE_ACTION, UNSUBSCRIBE_ACTION, SUBSCRIPTION_ACTION_TYPES
from mygpo.log import log

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, db_column='user_ptr_id')

    public_profile = models.BooleanField(default=True)
    generated_id = models.BooleanField(default=False)

    def __unicode__(self):
        return '%s (%s, %s)' % (self.user.username, self.public_profile, self.generated_id)

    class Meta:
        db_table = 'user'

class Podcast(models.Model):
    url = models.URLField(unique=True, verify_exists=False)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True, verify_exists=False)
    last_update = models.DateTimeField(null=True,blank=True)
    logo_url = models.CharField(max_length=1000,null=True,blank=True)
    author = models.CharField(max_length=100, null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)

    def subscriptions(self):
        return Subscription.objects.filter(podcast=self)

    def subscription_count(self):
        return self.subscriptions().count()

    def logo_shortname(self):
        return hashlib.sha1(self.logo_url).hexdigest()

    def subscribe_targets(self, user):
        """
        returns all Devices and SyncGroups on which this podcast can be subsrbied. This excludes all
        devices/syncgroups on which the podcast is already subscribed
        """
        targets = []

        devices = Device.objects.filter(user=user, deleted=False)
        for d in devices:
            subscriptions = [x.podcast for x in d.get_subscriptions()]
            if self in subscriptions: continue

            if d.sync_group:
                if not d.sync_group in targets: targets.append(d.sync_group)
            else:
                targets.append(d)

        return targets


    def __unicode__(self):
        return self.title if self.title != '' else self.url

    class Meta:
        db_table = 'podcast'


class ToplistEntry(models.Model):
    podcast = models.ForeignKey(Podcast)
    oldplace = models.IntegerField(db_column='old_place')
    subscriptions = models.IntegerField(db_column='subscription_count')

    def __unicode__(self):
        return '%s (%s)' % (self.podcast, self.subscriptions)

    class Meta:
        db_table = 'toplist'

class EpisodeToplistEntry(models.Model):
    episode = models.ForeignKey('Episode')
    listeners = models.PositiveIntegerField()

    def __unicode__(self):
        return '%s (%s)' % (self.episode, self.listeners)

    class Meta:
        db_table = 'episode_toplist'

class SuggestionEntry(models.Model):
    podcast = models.ForeignKey(Podcast)
    user = models.ForeignKey(User)
    priority = models.IntegerField()

    @staticmethod
    def forUser(user):
        subscriptions = [x.podcast for x in Subscription.objects.filter(user=user)]
        suggestions = SuggestionEntry.objects.filter(user=user).order_by('-priority')
        return [s for s in suggestions if s.podcast not in subscriptions]

    def __unicode__(self):
        return '%s (%s)' % (self.podcast, self.priority)

    class Meta:
        db_table = 'suggestion'


class Episode(models.Model):
    podcast = models.ForeignKey(Podcast)
    url = models.URLField(verify_exists=False)
    title = models.CharField(max_length=100, blank=True)
    description = models.TextField(null=True, blank=True)
    link = models.URLField(null=True, blank=True, verify_exists=False)
    timestamp = models.DateTimeField(null=True, blank=True)
    author = models.CharField(max_length=100, null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True)
    filesize = models.PositiveIntegerField(null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)


    def number(self):
        m = re.search('\D*(\d+)\D+', self.title)
        return m.group(1)

    def shortname(self):
        s = self.title
        s = s.replace(self.podcast.title, '')
        s = s.replace(self.number(), '')
        s = re.search('\W*(.+)', s).group(1)
        s = s.strip()
        return s


    def __unicode__(self):
        return '%s (%s)' % (self.shortname(), self.podcast)

    class Meta:
        db_table = 'episode'
        unique_together = ('podcast', 'url')

class SyncGroup(models.Model):
    """
    Devices that should be synced with each other need to be grouped
    in a SyncGroup.

    SyncGroups are automatically created by calling
    device.sync_with(other_device), but can also be created manually.

    device.sync() synchronizes the device for which the method is called
    with the other devices in its SyncGroup.
    """
    user = models.ForeignKey(User)

    def __unicode__(self):
        devices = [d.name for d in Device.objects.filter(sync_group=self)]
        return ', '.join(devices)

    def devices(self):
        return Device.objects.filter(sync_group=self)

    def add(self, device):
        if device.sync_group == self: return
        if device.sync_group != None:
            device.unsync()

        device.sync_group = self
        device.save()

    class Meta:
        db_table = 'sync_group'


class Device(models.Model):
    user = models.ForeignKey(User)
    uid = models.SlugField(max_length=50)
    name = models.CharField(max_length=100, blank=True)
    type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    sync_group = models.ForeignKey(SyncGroup, blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name if self.name else _('Unnamed Device (%s)' % self.uid)

    def get_subscriptions(self):
        self.sync()
        return Subscription.objects.filter(device=self)

    def sync(self):
        for s in self.get_sync_actions():
            try:
                SubscriptionAction.objects.create(device=self, podcast=s.podcast, action=s.action)
            except Exception, e:
                log('Error adding subscription action: %s (device %s, podcast %s, action %s)' % (str(e), repr(self), repr(s.podcast), repr(s.action)))

    def sync_targets(self):
        """
        returns all Devices and SyncGroups that can be used as a parameter for self.sync_with()
        """
        sync_targets = list(Device.objects.filter(user=self.user, sync_group=None, deleted=False).exclude(pk=self.id))

        sync_groups = SyncGroup.objects.filter(user=self.user)
        if self.sync_group != None: sync_groups = sync_groups.exclude(pk=self.sync_group.id)

        sync_targets.extend( list(sync_groups) )
        return sync_targets


    def get_sync_actions(self):
        """
        returns the SyncGroupSubscriptionActions correspond to the
        SubscriptionActions that need to be saved for the current device
        to synchronize it with its SyncGroup
        """
        if self.sync_group == None:
            return []

        devices = self.sync_group.devices().exclude(pk=self.id)

        sync_actions = self.latest_actions()

        for d in devices:
            a = d.latest_actions()
            for s in a.keys():
                if not sync_actions.has_key(s):
                    if a[s].action == SUBSCRIBE_ACTION:
                        sync_actions[s] = a[s]
                elif a[s].newer_than(sync_actions[s]) and (sync_actions[s].action != a[s].action):
                    sync_actions[s] = a[s]

        #remove actions that did not change
        current_state = self.latest_actions()
        for podcast in current_state.keys():
            if sync_actions[podcast] == current_state[podcast]:
               del sync_actions[podcast]

        return sync_actions.values()

    def latest_actions(self):
        """
        returns the latest action for each podcast
        that has an action on this device
        """
        #all podcasts that have an action on this device
        podcasts = [sa.podcast for sa in SubscriptionAction.objects.filter(device=self)]
        podcasts = list(set(podcasts)) #remove duplicates

        actions = {}
        for p in podcasts:
            actions[p] = self.latest_action(p)

        return actions

    def latest_action(self, podcast):
        """
        returns the latest action for the given podcast on this device
        """
        actions = SubscriptionAction.objects.filter(podcast=podcast,device=self).order_by('-timestamp', '-id')
        if actions.count() == 0:
            return None
        else:
            return actions[0]

    def sync_with(self, other):
        """
        set the device to be synchronized with other, which can either be a Device or a SyncGroup.
        this method places them in the same SyncGroup. get_sync_actions() can
        then return the SyncGroupSubscriptionActions for brining the device
        in sync with its group
        """
        if self.user != other.user:
            raise ValueError('the devices belong to different users')

        if isinstance(other, SyncGroup):
            other.add(self)
            self.save()
            return

        if self.sync_group == other.sync_group and self.sync_group != None:
            return

        if self.sync_group != None:
            if other.sync_group == None:
                self.sync_group.add(other)

            else:
                raise ValueError('the devices are in different sync groups')

        else:
            if other.sync_group == None:
                g = SyncGroup.objects.create(user=self.user)
                g.add(self)
                g.add(other)

            else:
                oter.sync_group.add(self)

    def unsync(self):
        """
        stops synchronizing the device
        this method removes the device from its SyncGroup. If only one
        device remains in the SyncGroup, it is removed so the device can
        be used in other groups.
        """
        if self.sync_group == None:
            raise ValueError('the device is not synced')

        g = self.sync_group
        print g
        self.sync_group = None
        self.save()

        devices = Device.objects.filter(sync_group=g)
        if devices.count() == 1:
            d = devices[0]
            d.sync_group = None
            d.save()
            g.delete()

    class Meta:
        db_table = 'device'

class EpisodeAction(models.Model):
    user = models.ForeignKey(User)
    episode = models.ForeignKey(Episode)
    device = models.ForeignKey(Device,null=True)
    action = models.CharField(max_length=10, choices=EPISODE_ACTION_TYPES)
    timestamp = models.DateTimeField(default=datetime.now)
    playmark = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return '%s %s %s' % (self.user, self.action, self.episode)

    def playmark_time(self):
        return datetime.fromtimestamp(float(self.playmark))

    class Meta:
        db_table = 'episode_log'


class Subscription(models.Model):
    device = models.ForeignKey(Device, primary_key=True)
    podcast = models.ForeignKey(Podcast)
    user = models.ForeignKey(User)
    subscribed_since = models.DateTimeField()

    def __unicode__(self):
        return '%s - %s on %s' % (self.device.user, self.podcast, self.device)

    def get_meta(self):
        #this is different than get_or_create because it does not necessarily create a new meta-object
        qs = SubscriptionMeta.objects.filter(user=self.user, podcast=self.podcast)

        if qs.count() == 0:
            return SubscriptionMeta(user=self.user, podcast=self.podcast)
        else:
            return qs[0]
            
    #this method has to be overwritten, if not it tries to delete a view
    def delete(self):
        pass
        
    class Meta:
        db_table = 'current_subscription'
        #not available in Django 1.0 (Debian stable)
        managed = False


class SubscriptionMeta(models.Model):
    user = models.ForeignKey(User)
    podcast = models.ForeignKey(Podcast)
    public = models.BooleanField(default=True)

    def __unicode__(self):
        return '%s - %s - %s' % (self.user, self.podcast, self.public)

    class Meta:
        db_table = 'subscription'
        unique_together = ('user', 'podcast')


class SubscriptionAction(models.Model):
    device = models.ForeignKey(Device)
    podcast = models.ForeignKey(Podcast)
    action = models.IntegerField(choices=SUBSCRIPTION_ACTION_TYPES)
    timestamp = models.DateTimeField(blank=True, default=datetime.now)

    def action_string(self):
        return 'subscribe' if self.action == SUBSCRIBE_ACTION else 'unsubscribe'

    def newer_than(self, action):
        return self.timestamp > action.timestamp

    def __unicode__(self):
        return '%s %s %s %s' % (self.device.user, self.device, self.action_string(), self.podcast)

    class Meta:
        db_table = 'subscription_log'
        unique_together = ('device', 'podcast', 'timestamp')


class URLSanitizingRule(models.Model):
    use_podcast = models.BooleanField()
    use_episode = models.BooleanField()
    search = models.CharField(max_length=100)
    search_precompiled = None
    replace = models.CharField(max_length=100, null=False, blank=True)
    priority = models.PositiveIntegerField()
    description = models.TextField(null=False, blank=True)

    class Meta:
        db_table = 'sanitizing_rules'

    def __unicode__(self):
        return '%s -> %s' % (self.search, self.replace)


