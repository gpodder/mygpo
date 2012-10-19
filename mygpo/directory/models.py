from django.core.cache import cache

from couchdbkit.ext.django.schema import *

from mygpo.utils import iterate_together
from mygpo.core.proxy import DocumentABCMeta
from mygpo.db.couchdb.podcast import podcasts_by_id


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


    def get_podcasts(self, start=0, end=20):
        cache_id = 'category-%s-%d-%d' % (self._id, start, end)

        podcasts = cache.get(cache_id)
        if podcasts:
            return podcasts

        ids = self.podcasts[start:end]
        podcasts = podcasts_by_id(ids)
        cache.set(cache_id, podcasts)

        return podcasts



    def save(self, *args, **kwargs):
        self.podcasts = sorted(self.podcasts, reverse=True)
        super(Category, self).save(*args, **kwargs)


    def get_weight(self):
        return len(self.podcasts)


    def get_tags(self):
        return self.spellings + [self.label]

    def __repr__(self):
        return '%s (+%d variants)' % (self.label, len(self.spellings))


class ExamplePodcasts(Document):
    podcast_ids  = StringListProperty()
    updated      = DateTimeProperty()
