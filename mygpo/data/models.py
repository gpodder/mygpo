from datetime import datetime

from django.db import models

from mygpo.podcasts.models import Podcast


class PodcastUpdateResult(models.Model):
    """ Results of a podcast update

    Once an instance is stored, the update is assumed to be finished. """

    # The podcast that was updated
    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE)

    # The timestamp at which the updated started to be executed
    start = models.DateTimeField(default=datetime.utcnow)

    # The duration of the update
    duration = models.DurationField()

    # A flad indicating whether the update was successful
    successful = models.BooleanField()

    # An error message. Should be empty if the update was successful
    error_message = models.TextField()

    # A flag indicating whether the update created the podcast
    podcast_created = models.BooleanField()

    # The number of episodes that were created by the update
    episodes_added = models.IntegerField()

    class Meta(object):

        get_latest_by = 'start'

        ordering = ['-start']

        indexes = [
            models.Index(fields=['podcast', 'start'])
        ]

