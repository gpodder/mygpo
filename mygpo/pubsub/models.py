from __future__ import unicode_literals

from django.db import models

from couchdbkit.ext.django.schema import *

from mygpo.podcasts.models import Podcast
from mygpo.core.models import UpdateInfoModel


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


class HubSubscription(UpdateInfoModel):
    """ A client-side PubSubHubbub subscription

    https://code.google.com/p/pubsubhubbub/ """

    SUBSCRIBE = 'subscribe'
    UNSUBSCRIBE = 'unsubscribe'

    MODE_CHOICES = (
        (SUBSCRIBE, 'subscribe'),
        (UNSUBSCRIBE, 'unsubscribe'),
    )

    # podcast to which the subscription belongs
    podcast = models.ForeignKey(Podcast, on_delete=models.PROTECT)

    # the topic of the subscription, ie the URL that was subscribed at the hub
    topic_url = models.CharField(max_length=2048, unique=True)

    # the URL of the hub
    hub_url = models.CharField(max_length=1000)

    # a token to verify the authenticity of the hub
    verify_token = models.CharField(max_length=32)

    # the last mode that was requested, either subscribe or unsubscribe
    mode = models.CharField(
        choices=MODE_CHOICES,
        max_length=max(map(len, [mode for mode, name in MODE_CHOICES])),
        blank=True,
    )

    # indicates whether the last mode change has already been verified
    verified = models.BooleanField(default=False)
