from couchdbkit.ext.django.schema import *

class Category(Document):
    label = StringProperty()
    updated = DateTimeProperty()
    spellings = StringListProperty()
    weight = IntegerProperty()

    @classmethod
    def for_tag(cls, tag):
        r = cls.view('directory/categories_by_tags', \
            key=tag, include_docs=True)
        return r.first() if r else None

    @classmethod
    def top_categories(cls, count):
        return cls.view('directory/categories', \
            descending=True, limit=count, include_docs=True)

    def get_tags(self):
        return self.spellings + [self.label]

    def __repr__(self):
        return '%s (+%d variants)' % (self.label, len(self.spellings))
