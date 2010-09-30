from couchdbkit import Document, StringProperty, DateTimeProperty, StringListProperty, IntegerProperty, Server

class Category(Document):
    label = StringProperty()
    updated = DateTimeProperty()
    spellings = StringListProperty()
    weight = IntegerProperty()

    @classmethod
    def for_tag(cls, tag):
        r = cls.view('directory/categories_by_tags', key=tag)
        return r.first() if r else None

    @classmethod
    def top_categories(cls, count):
        return cls.view('directory/categories', descending=True, limit=count)

    def get_tags(self):
        return self.spellings + [self.label]

    def __repr__(self):
        return '%s (+%d variants)' % (self.label, len(self.spellings))

server = Server()
db = server.get_or_create_db("mygpo")
Document.set_db(db)

