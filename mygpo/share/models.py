from random import random

from couchdbkit.ext.django.schema import *

from django.template.defaultfilters import slugify

from mygpo.core.proxy import DocumentABCMeta
from mygpo.users.models import RatingMixin
from mygpo.cache import cache_result



class PodcastList(Document, RatingMixin):
    """ A list of Podcasts that a user creates for the purpose of sharing """

    __metaclass__ = DocumentABCMeta

    title    = StringProperty(required=True)
    slug     = StringProperty(required=True)
    podcasts = StringListProperty()
    user     = StringProperty(required=True)
    random_key = FloatProperty(default=random)


    def __repr__(self):
        return '<{cls} "{title}" by {user}>'.format(
                cls=self.__class__.__name__, title=self.title, user=self.user)
