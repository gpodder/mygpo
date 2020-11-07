import uuid

from datetime import datetime

from django.db import models

from mygpo.core.models import UUIDModel
from mygpo.podcasts.models import Podcast


class PodcastUpdateResult(UUIDModel):
    """Results of a podcast update

    Once an instance is stored, the update is assumed to be finished."""

    # URL of the podcast to be updated
    podcast_url = models.URLField(max_length=2048)

    # The podcast that was updated
    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE, null=True)

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

        get_latest_by = "start"

        ordering = ["-start"]

        indexes = [models.Index(fields=["podcast", "start"])]

    def __str__(self):
        return 'Update Result for "{}" @ {:%Y-%m-%d %H:%M}'.format(
            self.podcast, self.start
        )

    # Use as context manager

    def __enter__(self):
        self.id = uuid.uuid4()
        self.start = datetime.utcnow()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.duration = datetime.utcnow() - self.start

        success = (exc_type, exc_value, traceback) == (None, None, None)
        self.successful = success

        if not success:
            self.error_message = str(exc_value)

            if self.podcast_created is None:
                self.podcast_created = False

            if self.episodes_added is None:
                self.episodes_added = 0

        self.save()
