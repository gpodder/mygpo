
from couchdbkit.ext.django.schema import *

from django.template.defaultfilters import slugify

from mygpo.core.proxy import DocumentABCMeta



class PodcastList(Document):
    """ A list of Podcasts that a user creates for the purpose of sharing """

    __metaclass__ = DocumentABCMeta

    title    = StringProperty(required=True)
    slug     = StringProperty(required=True)
    podcasts = StringListProperty()
    user     = StringProperty(required=True)


    @classmethod
    def for_user_slug(cls, user_id, slug):

        r = cls.view('share/lists_by_user_slug',
                key          = [user_id, slug],
                include_docs = True,
            )
        return r.first() if r else None


    @classmethod
    def for_user(cls, user_id):

        r = cls.view('share/lists_by_user_slug',
                startkey = [user_id, None],
                endkey   = [user_id, {}],
                include_docs = True,
            )
        return r.iterator()


    def __repr__(self):
        return '<{cls} "{title}" by {user}>'.format(
                cls=self.__class__.__name__, title=self.title, user=self.user)
