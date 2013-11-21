# -*- coding: utf-8 -*-
#
# PubSubHubbub subscriber mygpo
#
#

import urllib
import urllib2
import logging

from couchdbkit.ext.django import *
from django.core.urlresolvers import reverse

from mygpo.pubsub.models import Subscription, SubscriptionError
from mygpo.db.couchdb.pubsub import subscription_for_topic

logger = logging.getLogger(__name__)


def subscribe(feedurl, huburl, base_url, mode='subscribe'):
    """ Subscribe to the feed at a Hub """

    logger.info('subscribing for {feed} at {hub}'.format(feed=feedurl,
                                                             hub=huburl))
    verify = 'sync'

    subscription = subscription_for_topic(feedurl)
    if subscription is None:
        subscription = Subscription()
        subscription.verify_token = random_token()

    if subscription.mode == mode:
        if subscription.verified:
            logger.info('subscription already exists')
            return

    else:
        logger.info('subscription exists but has wrong mode: ' +
                    'old: %(oldmode)s, new: %(newmode)s. Overwriting.' %
                    dict(oldmode=subscription.mode, newmode=mode))

    subscription.url = feedurl
    subscription.mode = mode
    subscription.save()

    data = {
        "hub.callback":     callback_url(feedurl, base_url),
        "hub.mode":         mode,
        "hub.topic":        feedurl,
        "hub.verify":       verify,
        "hub.verify_token": subscription.verify_token,
    }

    data = urllib.urlencode(data.items())
    logger.debug('sending request: %s' % repr(data))

    resp = None

    try:
        resp = urllib2.urlopen(huburl, data)
    except urllib2.HTTPError, e:
        if e.code != 204:  # we actually expect a 204 return code
            msg = 'Could not send subscription to Hub: HTTP Error %d: %s' % (e.code, e.reason)
            logger.warn(msg)
            raise SubscriptionError(msg)
    except Exception, e:
        raise
        msg = 'Could not send subscription to Hub: %s' % repr(e)
        logger.warn(msg)
        raise SubscriptionError(msg)

    if resp:
        status = resp.code
        if status != 204:
            logger.warn('received incorrect status %d' % status)
            raise SubscriptionError('Subscription has not been accepted by '
                                    'the Hub')


def callback_url(feedurl, base_url):
    callback = reverse('pubsub-subscribe')
    param = urllib.urlencode([('url', feedurl)])
    return '{base}{callback}?{param}'.format(base=base_url, callback=callback,
                                             param=param)


def random_token(length=32):
    import random
    import string
    return "".join(random.sample(string.letters+string.digits, length))
