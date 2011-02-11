from django.db import models
from django.contrib.auth.models import User
from mygpo.api.models import Podcast, Episode, Device, PodcastGroup
from mygpo import settings


class PodcastTag(models.Model):
    tag = models.CharField(max_length=100)
    podcast = models.ForeignKey(Podcast)
    source = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True)
    weight = models.IntegerField(default=1)

    class Meta:
        db_table = 'podcast_tags'
        unique_together = ('podcast', 'source', 'user', 'tag')
        managed = False


# deprecated, only used in migration code
class HistoricPodcastData(models.Model):
    podcast = models.ForeignKey(Podcast)
    date = models.DateField()
    subscriber_count = models.IntegerField()

    class Meta:
        db_table = 'historic_podcast_data'
        unique_together = ('podcast', 'date')
        managed = False


class BackendSubscription(models.Model):
    """
    Represents the data in the subscriptions table, which
    contains all subscriptions, even those for currently deleted devices
    """
    device = models.ForeignKey(Device)
    podcast = models.ForeignKey(Podcast)
    user = models.ForeignKey(User)
    subscribed_since = models.DateTimeField()

    class Meta:
        unique_together = ('device', 'podcast', 'user')
        db_table = 'subscriptions'
        managed = False


class Listener(models.Model):
    device = models.ForeignKey(Device)
    user = models.ForeignKey(User)
    episode = models.ForeignKey(Episode)
    podcast = models.ForeignKey(Podcast)
    first_listened = models.DateTimeField()
    last_listened = models.DateTimeField()

    class Meta:
        db_table = 'listeners'
        managed = False


# Deprecated: only used in migration-code anymore
class RelatedPodcast(models.Model):
    ref_podcast = models.ForeignKey(Podcast, related_name='ref_podcast')
    rel_podcast = models.ForeignKey(Podcast, related_name='rel_podcast')
    priority = models.IntegerField()

    class Meta:
        db_table = 'related_podcasts'
        managed = False


# Deprecated: only used in migration-code anymore
class SuggestionBlacklist(models.Model):
    user = models.ForeignKey(User)
    podcast = models.ForeignKey(Podcast)

    class Meta:
        db_table = 'suggestion_blacklist'
        managed = False
