from django.db import models

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

class User(models.Model):
    username = models.SlugField(max_length=100)
    password = models.CharField(max_length=200)
    email = models.EmailField()
    public_profile = models.BooleanField()

    def __unicode__(self):
        return self.username
    
    class Meta:
        db_table = 'user'

class Podcast(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    link = models.URLField()
    last_update = models.DateTimeField()
    
    def subscriptions(self):
        return Subscription.objects.filter(podcast=self)
    
    def subscription_count(self):
        return self.subscriptions().count()

    def __unicode__(self):
        return self.title
    
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

class EpisodeAction(models.Model):
    user = models.ForeignKey(User, primary_key=True)
    episode = models.ForeignKey(Episode)
    action = models.CharField(max_length=10, choices=EPISODE_ACTION_TYPES)
    timestamp = models.DateTimeField()

    def __unicode__(self):
        return '%s %s %s' % self.user, self.action, self.episode

    class Meta:
        db_table = 'episode_log'

class Device(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=DEVICE_TYPES)

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.type)
    
    class Meta:
        db_table = 'device'

class Subscription(models.Model):
    device = models.ForeignKey(Device, primary_key=True)
    podcast = models.ForeignKey(Podcast)

    def __unicode__(self):
        return '%s - %s on %s' % (self.device.user, self.podcast, self.device)
    
    class Meta:
        db_table = 'current_subscription'

class SubscriptionAction(models.Model):
    device = models.ForeignKey(Device, primary_key=True)
    podcast = models.ForeignKey(Podcast)
    action = models.CharField(max_length=12, choices=SUBSCRIPTION_ACTION_TYPES)
    timestamp = models.DateTimeField()

    def __unicode__(self):
        return '%s %s %s' % (self.device, self.action, self.podcast)
    
    class Meta:
        db_table = 'subscription_log'

