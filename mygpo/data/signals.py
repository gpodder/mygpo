from django.dispatch import receiver

from mygpo.pubsub.signals import subscription_updated
from mygpo.data.tasks import update_podcasts

import logging
logger = logging.getLogger(__name__)


@receiver(subscription_updated, dispatch_uid='update_podcast-pubsub')
def update_podcast(sender, **kwargs):
    """ update podcast in background when receiving pubsub-notification """

    logger.info('updating podcast for "%s" after pubsub notification', sender)
    update_podcasts.delay([sender])
