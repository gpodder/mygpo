from __future__ import unicode_literals

from couchdbkit.ext.django.schema import *

# make sure this code is executed at startup
from mygpo.pubsub.signals import *


class SubscriptionError(Exception):
    pass

class Subscription(Document):
    url          = StringProperty(required=True)
    verify_token = StringProperty(required=True)
    mode         = StringProperty(required=True)
    verified     = BooleanProperty(default=False)


    def __unicode__(self):
        if self.verified:
            verified = u'verified'
        else:
            verified = u'unverified'
        return u'<Subscription for %s: %s>' % (self.url, verified)

    def __str__(self):
        return str(unicode(self))
