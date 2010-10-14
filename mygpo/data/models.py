from django.db import models
from django.contrib.auth.models import User
from mygpo.api.models import Podcast, Episode, Device, PodcastGroup
from mygpo import settings


class PodcastTagManager(models.Manager):

    def top_tags_for_podcast(self, podcast):
        """
        returns the most-assigned tags for the given podcast
        """
        tags = PodcastTag.objects.filter(podcast=podcast)
        return self.top_tags(tags)

    def top_tags(self, tags=None):
        """
        returns the most-assigned tags

        If param tags is given, it is expected to be a PodcastTag-QuerySet.
        The method is then restricted to this QuerySet, otherwise all tags
        are considered
        """
        if not tags:
            tags = PodcastTag.objects.all()
        tags = tags.values('tag').annotate(count=models.Count('id'))
        tags = sorted(tags, key=lambda x: x['count'], reverse=True)
        return tags


class PodcastTag(models.Model):
    tag = models.CharField(max_length=100)
    podcast = models.ForeignKey(Podcast)
    source = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True)
    weight = models.IntegerField(default=1)

    objects = PodcastTagManager()

    class Meta:
        db_table = 'podcast_tags'
        unique_together = ('podcast', 'source', 'user', 'tag')
        managed = False


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


class RelatedPodcast(models.Model):
    ref_podcast = models.ForeignKey(Podcast, related_name='ref_podcast')
    rel_podcast = models.ForeignKey(Podcast, related_name='rel_podcast')
    priority = models.IntegerField()

    class Meta:
        db_table = 'related_podcasts'
        managed = False


class SuggestionBlacklist(models.Model):
    user = models.ForeignKey(User)
    podcast = models.ForeignKey(Podcast)

    class Meta:
        db_table = 'suggestion_blacklist'
        managed = False


class DirectoryEntryManager(models.Manager):

    def top_tags(self, total):
        tags = self.raw("select *, count(id) as entries from podcast_tags group by tag order by entries desc")[:total]

        tags = filter(lambda x: not x.tag.startswith('http://'), tags)

        excluded_tags = getattr(settings, 'DIRECTORY_EXCLUDED_TAGS', [])
        return filter(lambda x: not x.tag in excluded_tags, tags)

    def podcasts_for_category(self, tags):
        return DirectoryEntry.objects.filter(tag__in=tags).order_by('-ranking')

class DirectoryEntry(models.Model):
    podcast = models.ForeignKey(Podcast, null=True)
    podcast_group = models.ForeignKey(PodcastGroup, null=True)
    tag = models.CharField(max_length=100)
    ranking = models.FloatField()

    objects = DirectoryEntryManager()

    def get_item(self):
        if self.podcast:
            return self.podcast
        else:
            return self.podcast_group

    def get_podcast(self):
        """
        Returns a podcast which is representative for this toplist-entry
        If the entry is a non-grouped podcast, it is returned
        If the entry is a podcast group, one of its podcasts is returned
        """
        if self.podcast:
            return self.podcast
        else:
            return self.podcast_group.podcasts()[0]

    class Meta:
        db_table = 'directory_entries'
        managed = False


from mygpo.data.signals import update_podcast_tag_entry
from django.db.models.signals import post_save, pre_delete

post_save.connect(update_podcast_tag_entry, sender=PodcastTag)
pre_delete.connect(update_podcast_tag_entry, sender=PodcastTag)

