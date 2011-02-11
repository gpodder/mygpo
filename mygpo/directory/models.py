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
        for p, w in podcasts:

            updated = False

            for e in self.podcasts:
                if p == e.podcast:
                    e.weight += w
                    updated = True
                    break

            if not updated:
                entry = CategoryEntry()
                entry.podcast = p
                entry.weight = float(w)
                self.podcasts.append(entry)


    def get_podcasts(self, start=0, end=20):
        podcast_ids = [e.podcast for e in self.podcasts[start:end]]
        return map(Podcast.for_id, podcast_ids)


    def save(self, *args, **kwargs):
        self.podcasts = sorted(self.podcasts, reverse=True)
        super(Category, self).save(*args, **kwargs)


    def get_weight(self):
        return sum([e.weight for e in self.podcasts])


    def get_tags(self):
        return self.spellings + [self.label]

    def __repr__(self):
        return '%s (+%d variants)' % (self.label, len(self.spellings))
