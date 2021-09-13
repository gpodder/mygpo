from datetime import datetime

from django.shortcuts import get_object_or_404

from mygpo.podcasts.models import Podcast
from mygpo.api import APIView, RequestException
from mygpo.api.httpresponse import JsonResponse
from mygpo.api.backend import get_device
from mygpo.utils import get_timestamp, normalize_feed_url, intersect
from mygpo.users.models import Client
from mygpo.subscriptions.tasks import subscribe, unsubscribe
from mygpo.subscriptions import get_subscription_history, subscription_diff
from mygpo.api.basic_auth import require_valid_user, check_username

import logging

logger = logging.getLogger(__name__)


class SubscriptionsAPI(APIView):
    """API for sending and retrieving podcast subscription updates"""

    def get(self, request, version, username, device_uid):
        """Client retrieves subscription updates"""
        now = datetime.utcnow()
        user = request.user
        device = get_object_or_404(Client, user=user, uid=device_uid)
        since = self.get_since(request)
        add, rem, until = self.get_changes(user, device, since, now)
        return JsonResponse({"add": add, "remove": rem, "timestamp": until})

    def post(self, request, version, username, device_uid):
        """Client sends subscription updates"""
        now = get_timestamp(datetime.utcnow())
        logger.info(
            "Subscription Upload @{username}/{device_uid}".format(
                username=request.user.username, device_uid=device_uid
            )
        )

        d = get_device(
            request.user, device_uid, request.META.get("HTTP_USER_AGENT", "")
        )

        actions = self.parsed_body(request)

        add = list(filter(None, actions.get("add", [])))
        rem = list(filter(None, actions.get("remove", [])))
        logger.info(
            "Subscription Upload @{username}/{device_uid}: add "
            "{num_add}, remove {num_remove}".format(
                username=request.user.username,
                device_uid=device_uid,
                num_add=len(add),
                num_remove=len(rem),
            )
        )

        update_urls = self.update_subscriptions(request.user, d, add, rem)

        return JsonResponse({"timestamp": now, "update_urls": update_urls})

    def update_subscriptions(self, user, device, add, remove):

        conflicts = intersect(add, remove)
        if conflicts:
            msg = "can not add and remove '{}' at the same time".format(str(conflicts))
            logger.warning(msg)
            raise RequestException(msg)

        add_s = list(map(normalize_feed_url, add))
        rem_s = list(map(normalize_feed_url, remove))

        assert len(add) == len(add_s) and len(remove) == len(rem_s)

        pairs = zip(add + remove, add_s + rem_s)
        updated_urls = list(filter(lambda pair: pair[0] != pair[1], pairs))

        add_s = filter(None, add_s)
        rem_s = filter(None, rem_s)

        # If two different URLs (in add and remove) have
        # been sanitized to the same, we ignore the removal
        rem_s = filter(lambda x: x not in add_s, rem_s)

        for add_url in add_s:
            podcast = Podcast.objects.get_or_create_for_url(add_url).object
            subscribe(podcast.pk, user.pk, device.uid, add_url)

        remove_podcasts = Podcast.objects.filter(urls__url__in=rem_s)
        for podcast in remove_podcasts:
            unsubscribe(podcast.pk, user.pk, device.uid)

        return updated_urls

    def get_changes(self, user, device, since, until):
        """Returns subscription changes for the given device"""
        history = get_subscription_history(user, device, since, until)
        logger.info("Subscription History: {num}".format(num=len(history)))

        add, rem = subscription_diff(history)
        logger.info(
            "Subscription Diff: +{num_add}/-{num_remove}".format(
                num_add=len(add), num_remove=len(rem)
            )
        )

        until_ = get_timestamp(until)

        # TODO: we'd need to get the ref_urls here somehow
        add_urls = [p.url for p in add]
        rem_urls = [p.url for p in rem]
        return (add_urls, rem_urls, until_)
