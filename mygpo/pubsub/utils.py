# -*- coding: utf-8 -*-
#
# PubSubHubbub subscriber mygpo
#
#

import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import logging

from django.core.urlresolvers import reverse

from mygpo.utils import random_token
from mygpo.pubsub.models import HubSubscription, SubscriptionError

logger = logging.getLogger(__name__)


def subscribe(podcast, feedurl, huburl, base_url, mode='subscribe'):
    """ Subscribe to the feed at a Hub """

    logger.info('subscribing for {feed} at {hub}'.format(feed=feedurl,
                                                         hub=huburl))
    verify = 'sync'

    token_max_len = HubSubscription._meta.get_field('verify_token').max_length
    subscription, created = HubSubscription.objects.get_or_create(
        topic_url=feedurl,
        defaults={
            'verify_token': random_token(token_max_len),
            'mode': '',
            'podcast': podcast,
        }
    )

    if subscription.mode == mode:
        if subscription.verified:
            logger.info('subscription already exists')
            return

    else:
        logger.info('subscription exists but has wrong mode: ' +
                    'old: %(oldmode)s, new: %(newmode)s. Overwriting.' %
                    dict(oldmode=subscription.mode, newmode=mode))

    subscription.topic_url = feedurl
    subscription.mode = mode
    subscription.save()

    data = {
        "hub.callback":     callback_url(feedurl, base_url),
        "hub.mode":         mode,
        "hub.topic":        feedurl,
        "hub.verify":       verify,
        "hub.verify_token": subscription.verify_token,
    }

    data = urllib.parse.urlencode(list(data.items()))
    logger.debug('sending request: %s' % repr(data))

    resp = None

    try:
        resp = urllib.request.urlopen(huburl, data)

    except urllib.error.HTTPError as e:
        if e.code != 204:  # we actually expect a 204 return code
            msg = 'Could not send subscription to Hub: HTTP Error %d: %s' % \
                (e.code, e.reason)
            logger.warn(msg)
            raise SubscriptionError(msg)

    except Exception as e:
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
    param = urllib.parse.urlencode([('url', feedurl)])
    return '{base}{callback}?{param}'.format(base=base_url, callback=callback,
                                             param=param)
