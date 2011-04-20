from couchdbkit.ext.django.schema import *

from mygpo.core.models import Podcast
from mygpo.utils import iterate_together


class CategoryEntry(DocumentSchema):
    podcast = StringProperty()
    weight = FloatProperty()

    def __repr__(self):
        return 'Podcast %s in Category %s' % (self.podcast, self._id)

    def __cmp__(self, other):
        return cmp(self.weight, other.weight)


class Category(Document):
    label = StringProperty()
    updated = DateTimeProperty()
    spellings = StringListProperty()
    podcasts = SchemaListProperty(CategoryEntry)

    @classmethod
    def for_tag(cls, tag):
        r = cls.view('directory/categories_by_tags', \
            key=tag, include_docs=True)
        return r.first() if r else None

    @classmethod
    def top_categories(cls, count):
        return cls.view('directory/categories', \
            descending=True, limit=count, include_docs=True)


    def merge_podcasts(self, podcasts):
        """
        Merges some entries into the current category.
        """

        cmp_entry_podcasts = lambda e1, e2: cmp(e1.podcast, e2.podcast)

        podcasts = sorted(podcasts, cmp=cmp_entry_podcasts)
        self.podcasts = sorted(self.podcasts, cmp=cmp_entry_podcasts)

        new_entries = []

        for e1, e2 in iterate_together(self.podcasts, podcasts, compare=cmp_entry_podcasts):
            if e1 is None:
                new_entries.append(e2)

            elif e2 is None:
                new_entries.append(e1)

            else:
                new_entries.append( max(e1, e2) )

        self.podcasts = new_entries


    def get_podcast_ids(self, start=0, end=20):
        return [e.podcast for e in self.podcasts[start:end]]


    def get_podcasts(self, start=0, end=20):
        return Podcast.get_multi(self.get_podcast_ids(start, end))



    def save(self, *args, **kwargs):
        self.podcasts = sorted(self.podcasts, reverse=True)
        super(Category, self).save(*args, **kwargs)


    def get_weight(self):
        return sum([e.weight for e in self.podcasts])


    def get_tags(self):
        return self.spellings + [self.label]

    def __repr__(self):
        return '%s (+%d variants)' % (self.label, len(self.spellings))
