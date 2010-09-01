from django.db import models
from mygpo.api.models import Podcast, PodcastGroup
import shlex


class SearchEntryManager(models.Manager):

    def search(self, q):
        qs = SearchEntry.objects.all()
        try:
            tokens = shlex.split(q)
        except ValueError:
            tokens = [q]

        for query in tokens:
            qs = qs.filter(text__icontains=query)

        return qs.order_by('-priority')


class SearchEntry(models.Model):
    text = models.TextField(db_index=True)
    obj_type = models.CharField(max_length=20, db_index=True)
    obj_id = models.IntegerField(db_index=True)
    tags = models.CharField(max_length=200, db_index=True)
    priority = models.IntegerField(db_index=True)

    objects = SearchEntryManager()

    def __repr__(self):
        return "<%s '%s'>" % (self.__class__.__name__, self.text[:20])


    def get_object(self):
        if self.obj_type == 'podcast':
            return Podcast.objects.get(id=self.obj_id)
        elif self.obj_type == 'podcast_group':
            return PodcastGroup.objects.get(id=self.obj_id)
        else:
            return None

    def get_podcast(self):
        """
        Returns a podcast which is representative for this search-result
        If the entry is a non-grouped podcast, it is returned
        If the entry is a podcast group, one of its podcasts is returned
        """
        obj = self.get_object()

        if isinstance(obj, Podcast):
            return obj
        elif isinstance(obj, PodcastGroup):
            return obj.podcasts()[0]
        else:
            return None

