from __future__ import unicode_literals

from django.db import models
from django.core.cache import cache

from couchdbkit.ext.django.schema import *

from mygpo.podcasts.models import Podcast
from mygpo.utils import iterate_together
from mygpo.core.models import UpdateInfoModel, OrderedModel
from mygpo.core.proxy import DocumentABCMeta


class Category(Document):

    __metaclass__ = DocumentABCMeta

    label = StringProperty(required=True)
    updated = DateTimeProperty(required=True)
    spellings = StringListProperty()
    podcasts = ListProperty()


    def merge_podcasts(self, podcasts):
        """
        Merges some entries into the current category.
        """

        key = lambda e: e.podcast

        podcasts = sorted(podcasts, key=key)
        self.podcasts = sorted(self.podcasts, key=key)

        new_entries = []

        for e1, e2 in iterate_together([self.podcasts, podcasts], key):
            if e1 is None:
                new_entries.append(e2)

            elif e2 is None:
                new_entries.append(e1)

            else:
                new_entries.append( max(e1, e2) )

        self.podcasts = new_entries


    # called from within a template where we can't pass parameters
    def get_podcasts_more(self, start=0, end=40):
        return self.get_podcasts(start, end)


    def get_podcasts(self, start=0, end=10):
        cache_id = 'category-%s-%d-%d' % (self._id, start, end)

        podcasts = cache.get(cache_id)
        if podcasts:
            return podcasts

        ids = self.podcasts[start:end]

        # TODO: this should not be needed anymore after migration
        if ids and not isinstance(ids[0], unicode):
            return []

        podcasts = Podcast.objects.filter(id__in=ids)
        cache.set(cache_id, podcasts)

        return podcasts


    def get_weight(self):
        return getattr(self, '_weight', len(self.podcasts))


    def get_tags(self):
        return self.spellings + [self.label]

    def __repr__(self):
        return '%s (+%d variants)' % (self.label, len(self.spellings))


class ExamplePodcastsManager(models.Manager):
    """ Manager fo the ExamplePodcast model """

    def get_podcasts(self):
        """ The example podcasts """
        return Podcast.objects.filter(examplepodcast__isnull=False)\
                              .order_by('examplepodcast__order')


class ExamplePodcast(UpdateInfoModel, OrderedModel):
    """ Example podcasts returned by the API """

    podcast = models.ForeignKey(Podcast)

    objects = ExamplePodcastsManager()

    class Meta(OrderedModel.Meta):
        unique_together = [
            ('order', )
        ]
