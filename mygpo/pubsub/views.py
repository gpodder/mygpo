# -*- coding: utf-8 -*-
#
# PubSubHubbub subscriber for mygpo
#
#

import logging

from django.http import HttpResponseNotFound, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from mygpo.pubsub.models import HubSubscription
from mygpo.pubsub.signals import subscription_updated

logger = logging.getLogger(__name__)


class SubscribeView(View):
    """ Endpoint for Pubsubhubbub subscriptions """

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(SubscribeView, self).dispatch(*args, **kwargs)

    def get(self, request):
        """ Callback used by the Hub to verify the subscription request """

        # received arguments: hub.mode, hub.topic, hub.challenge,
        # hub.lease_seconds, hub.verify_token
        mode = request.GET.get("hub.mode")
        feed_url = request.GET.get("hub.topic")
        challenge = request.GET.get("hub.challenge")
        lease_seconds = request.GET.get("hub.lease_seconds")
        verify_token = request.GET.get("hub.verify_token")

        logger.debug(
            (
                "received subscription-parameters: mode: %(mode)s, "
                + "topic: %(topic)s, challenge: %(challenge)s, lease_seconds: "
                + "%(lease_seconds)s, verify_token: %(verify_token)s"
            )
            % dict(
                mode=mode,
                topic=feed_url,
                challenge=challenge,
                lease_seconds=lease_seconds,
                verify_token=verify_token,
            )
        )

        try:
            subscription = HubSubscription.objects.get(topic_url=feed_url)

        except HubSubscription.DoesNotExist:
            logger.warning("subscription does not exist")
            return HttpResponseNotFound()

        if subscription.mode != mode:
            logger.warning("invalid mode, %s expected" % subscription.mode)
            return HttpResponseNotFound()

        if subscription.verify_token != verify_token:
            logger.warning(
                "invalid verify_token, %s expected" % subscription.verify_token
            )
            return HttpResponseNotFound()

        subscription.verified = True
        subscription.save()

        logger.info("subscription confirmed")
        return HttpResponse(challenge)

    def post(self, request):
        """ Callback to notify about a feed update """

        feed_url = request.GET.get("url")

        if not feed_url:
            logger.info("received notification without url")
            return HttpResponse(status=400)

        logger.info("received notification for %s" % feed_url)

        try:
            subscription = HubSubscription.objects.get(topic_url=feed_url)

        except HubSubscription.DoesNotExist:
            logger.warning("no subscription for this URL")
            return HttpResponse(status=400)

        if subscription.mode != "subscribe":
            logger.warning("invalid subscription mode: %s" % subscription.mode)
            return HttpResponse(status=400)

        if not subscription.verified:
            logger.warning("the subscription has not yet been verified")
            return HttpResponse(status=400)

        subscription_updated.send(sender=feed_url)

        return HttpResponse(status=200)
