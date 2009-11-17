from django.db import models
from django.contrib.auth.models import User, UserManager
from datetime import datetime
import hashlib

EPISODE_ACTION_TYPES = (
        ('download', 'downloaded'),
        ('play',     'played'),
        ('sync',     'synced'),
        ('lock',     'locked'),
        ('delete',   'deleted')
    )

DEVICE_TYPES = (
        ('desktop', 'Desktop'),
        ('laptop', 'Laptop'),
        ('mobile', 'Mobile'),
        ('server', 'Server'),
        ('other', 'Other')
    )

SUBSCRIPTION_ACTION_TYPES = (
        ('subscribe', 'subscribed'),
        ('unsubscribe', 'unsubscribed')
    )

#inheriting from User, as described in 
#http://scottbarnham.com/blog/2008/08/21/extending-the-django-user-model-with-inheritance/
class UserAccount(User):
    public_profile = models.BooleanField()
    generated_id = models.BooleanField()

    objects = UserManager()

    def __unicode__(self):
        return self.username
    
    class Meta:
        db_table = 'user'

class Podcast(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    link = models.URLField()
    last_update = models.DateTimeField(null=True,blank=True)
    logo_url = models.CharField(max_length=1000)
    
    def subscriptions(self):
        return Subscription.objects.filter(podcast=self)
    
    def subscription_count(self):
        return self.subscriptions().count()

    def logo_shortname(self):
        return hashlib.sha1(self.logo_url).hexdigest()

    def __unicode__(self):
        return self.title if self.title != '' else self.url
    
    class Meta:
        db_table = 'podcast'

class Episode(models.Model):
    podcast = models.ForeignKey(Podcast)
    url = models.URLField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    link = models.URLField()

    def __unicode__(self):
        return self.title
    
    class Meta:
        db_table = 'episode'

class SyncGroup(models.Model):
    user = models.ForeignKey(User)
    
    def __unicode__(self):
        devices = [d.name for d in Device.objects.filter(sync_group=self)]
        return '%s - %s' % (self.user, ', '.join(devices))
             
    class Meta:
        db_table = 'sync_group'


class Device(models.Model):
    user = models.ForeignKey(User)
    uid = models.SlugField(max_length=50)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    sync_group = models.ForeignKey(SyncGroup, blank=True, null=True)

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.type)

    def get_subscriptions(self):
        self.sync()
        return Subscription.objects.filter(device=self)

    def sync(self):
        for s in self.get_sync_actions():
            SubscriptionAction.objects.create(device=self, podcast=s.podcast, timestamp=s.timestamp, action=s.action)

    def get_sync_actions(self):
        """
        returns the SyncGroupSubscriptionActions correspond to the
        SubscriptionActions that need to be saved for the current device
        to synchronize it with its SyncGroup
        """
        all_sync_actions = SyncGroupSubscriptionAction.objects.filter(sync_group=self.sync_group)
        podcasts = [p.podcast for p in Subscription.objects.filter(device=self)]
        sync_actions = []
        for s in all_sync_actions:
            a = self.latest_action(s.podcast)

            if a != None and s.timestamp <= a.timestamp: continue

            if s.action == 'subscribe' and not s.podcast in podcasts:
                sync_actions.append(s)
            elif s.action == 'unsubscribe' and s.podcast in podcasts:
                sync_actions.append(s)
        return sync_actions

    def latest_action(self, podcast):
        actions = SubscriptionAction.objects.filter(podcast=podcast,device=self).order_by('-timestamp')
        if len(actions) == 0:
            return None
        else:
            return actions[0]

    def sync_with(self, other):
        """
        set the device to be synchronized with the other device.
        this method places them in the same SyncGroup. get_sync_actions() can 
        then return the SyncGroupSubscriptionActions for brining the device 
        in sync with its group
        """
        if self.user != other.user:
            raise ValueError('the devices belong to different users')

        if self.sync_group == other.sync_group and self.sync_group != None:
            return

        if self.sync_group != None:
            if other.sync_group == None:
                other.sync_group = self.sync_group
                other.save

            else:
                raise ValueError('the devices are in different sync groups')

        else:
            if other.sync_group == None:
                g = SyncGroup.objects.create(user=self.user)
                self.sync_group=g
                self.save()
                other.sync_group=g
                other.save()

            else:
                self.syn_group = other.sync_group
                self.save()

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
    user = models.ForeignKey(User, primary_key=True)
    episode = models.ForeignKey(Episode)
    device = models.ForeignKey(Device)
    action = models.CharField(max_length=10, choices=EPISODE_ACTION_TYPES)
    timestamp = models.DateTimeField(default=datetime.now)
    playmark = models.IntegerField()

    def __unicode__(self):
        return '%s %s %s' % self.user, self.action, self.episode

    class Meta:
        db_table = 'episode_log'


class Subscription(models.Model):
    device = models.ForeignKey(Device, primary_key=True)
    podcast = models.ForeignKey(Podcast)
    user = models.ForeignKey(UserAccount)
    subscribed_since = models.DateTimeField()

    def __unicode__(self):
        return '%s - %s on %s' % (self.device.user, self.podcast, self.device)
    
    class Meta:
        db_table = 'current_subscription'

class SubscriptionActionBase(models.Model):
    device = models.ForeignKey(Device)
    podcast = models.ForeignKey(Podcast)
    action = models.CharField(max_length=12, choices=SUBSCRIPTION_ACTION_TYPES)
    timestamp = models.DateTimeField(blank=True, default=datetime.now)

    def __unicode__(self):
        return '%s %s %s' % (self.device, self.action, self.podcast)

    class Meta:
        abstract = True
        unique_together = ('device', 'podcast', 'action', 'timestamp')

class SubscriptionAction(SubscriptionActionBase):
    
    class Meta:
        db_table = 'subscription_log'

class SyncGroupSubscriptionAction(SubscriptionActionBase):
    """ READ ONLY MODEL """
    sync_group = models.ForeignKey(SyncGroup)

    def save(self, **kwargs):
        raise NotImplementedError

    class Meta:
        db_table = 'sync_group_subscription_log'

