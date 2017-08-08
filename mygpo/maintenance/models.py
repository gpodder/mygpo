from django.db import models

from mygpo.core.models import UUIDModel
from mygpo.podcasts.models import Podcast


class MergeQueue(UUIDModel):
    """ A Group of podcasts that could be merged """


class MergeQueueEntry(UUIDModel):
    """ An entry in a MergeQueue """

    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE)

    queue = models.ForeignKey(MergeQueue, on_delete=models.CASCADE)

    class Meta:
        unique_together = [
            ['podcast', ]  # a podcast can only belong to one queue
        ]
