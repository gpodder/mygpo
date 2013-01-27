from random import random

from couchdbkit.ext.django.schema import *

from django.core.urlresolvers import reverse

from mygpo.core.proxy import DocumentABCMeta
from mygpo.users.models import RatingMixin
from mygpo.flattr import FlattrThing



class PodcastList(Document, RatingMixin):
    """ A list of Podcasts that a user creates for the purpose of sharing """

    __metaclass__ = DocumentABCMeta

    title    = StringProperty(required=True)
    slug     = StringProperty(required=True)
    podcasts = StringListProperty()
    user     = StringProperty(required=True)
    random_key = FloatProperty(default=random)


    def get_flattr_thing(self, domain, username):
        """ Returns a "Thing" which can be flattred by other Flattr users """
        return FlattrThing(
                url = reverse('list-show', args=[username, self.slug]),
                title = self.title,
                description = u'A collection of podcasts about "%s" by %s user %s' % (self.title, domain, username),
                category = u'audio',
                hidden = None,
                tags = None,
                language = None,
            )


    def __repr__(self):
        return '<{cls} "{title}" by {user}>'.format(
                cls=self.__class__.__name__, title=self.title, user=self.user)
