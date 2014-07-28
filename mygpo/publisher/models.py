""" This module contains models for the publisher pages """

from django.db import models
from django.conf import settings

from mygpo.podcasts.models import Podcast

import logging
logger = logging.getLogger(__name__)


class PublishedPodcastManager(models.Manager):
    """ Manager for the PublishedPodcast model """

    def publish_podcasts(self, user, podcasts):
        existed, created = 0, 0
        for podcast in podcasts:
            pp, _ = PublishedPodcast.objects.get_or_create(
                publisher=user,
                podcast=podcast,
            )

            if created:
                created += 1
                logger.info('Created publisher permissions for %r on %r',
                            user, podcast)
            else:
                existed += 1
                logger.info('Publisher permissions for %r on %r already exist',
                            user, podcast)


        return created, existed


class PublishedPodcast(models.Model):
    publisher = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.CASCADE)
    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ('publisher', 'podcast'),
        )

    objects = PublishedPodcastManager()
