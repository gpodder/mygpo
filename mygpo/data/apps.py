from django.apps import AppConfig
from mygpo.pubsub.signals import subscription_updated

import logging
logger = logging.getLogger(__name__)


def update_podcast(sender, **kwargs):
    """ update podcast in background when receiving pubsub-notification """
    from mygpo.data.tasks import update_podcasts
    logger.info('updating podcast for "%s" after pubsub notification', sender)
    update_podcasts.delay([sender])


class DataAppConfig(AppConfig):
    name = 'mygpo.data'

    def ready(self):
        subscription_updated.connect(update_podcast,
                                     dispatch_uid='update_podcast-pubsub')
