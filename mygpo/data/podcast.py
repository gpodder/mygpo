from collections import Counter
import random
import logging

from django.conf import settings

from mygpo.podcasts.models import Podcast
from mygpo.subscriptions.models import Subscription
from mygpo.pubsub import utils

logger = logging.getLogger(__name__)


def calc_similar_podcasts(podcast, num=20, user_sample=100):
    """Get a list of podcasts that seem to be similar to the given one.

    The similarity is based on similar subscriptions; for performance
    reasons, only a sample of subscribers is considered"""

    logger.info("Calculating podcasts similar to {podcast}".format(podcast=podcast))

    # get all users that subscribe to this podcast
    user_ids = (
        Subscription.objects.filter(podcast=podcast)
        .order_by("user")
        .distinct("user")
        .values_list("user", flat=True)
    )
    logger.info(
        "Found {num_subscribers} subscribers, taking a sample "
        "of {sample_size}".format(
            num_subscribers=len(user_ids), sample_size=user_sample
        )
    )

    # take a random sample of ``user_sample`` subscribers
    user_ids = list(user_ids)  # evaluate ValuesQuerySet
    random.shuffle(user_ids)
    user_ids = user_ids[:user_sample]

    # get other podcasts that the user sample subscribes to
    podcasts = Counter()
    for user_id in user_ids:
        subscriptions = (
            Podcast.objects.filter(subscription__user__id__in=user_ids)
            .distinct("pk")
            .exclude(pk=podcast.pk)
        )
        podcasts.update(Counter(subscriptions))
    logger.info(
        "Found {num_podcasts}, returning top {num_results}".format(
            num_podcasts=len(podcasts), num_results=num
        )
    )

    return podcasts.most_common(num)


def subscribe_at_hub(podcast):
    """Tries to subscribe to the given podcast at its hub"""

    if not podcast.hub:
        return

    base_url = settings.DEFAULT_BASE_URL

    if not base_url:
        logger.warning(
            "Could not subscribe to podcast {podcast} "
            "at hub {hub} because DEFAULT_BASE_URL is not "
            "set.".format(podcast=podcast, hub=podcast.hub)
        )
        return

    logger.info(
        "subscribing to {podcast} at {hub}.".format(podcast=podcast, hub=podcast.hub)
    )
    utils.subscribe(podcast, podcast.url, podcast.hub, base_url)
