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
    
    class Meta:
        db_table = 'user'

class Podcast(models.Model):
    url = models.URLField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    link = models.URLField()
    last_update = models.DateTimeField()
    
    class Meta:
        db_table = 'podcast'

class Episode(models.Model):
    podcast = models.ForeignKey(Podcast)
    url = models.URLField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    link = models.URLField()
    
    class Meta:
        db_table = 'episode'

class EpisodeAction(models.Model):
    db_table = 'episode_log'
    
    user = models.ForeignKey(User)
    episode = models.ForeignKey(Episode)
    action = models.CharField(max_length=10, choices=EPISODE_ACTION_TYPES)
    timestamp = models.DateTimeField()

class Device(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=DEVICE_TYPES)
    
    class Meta:
        db_table = 'device'

class Subscription(models.Model):
    user = models.ForeignKey(User)
    podcast = models.ForeignKey(Podcast)
    
    class Meta:
        db_table = 'current_subscription'

class SubscriptionAction(models.Model):
    device = models.ForeignKey(Device)
    podcast = models.ForeignKey(Podcast)
    action = models.CharField(max_length=12, choices=SUBSCRIPTION_ACTION_TYPES)
    timestamp = models.DateTimeField()
    
    class Meta:
        db_table = 'subscription_log'

