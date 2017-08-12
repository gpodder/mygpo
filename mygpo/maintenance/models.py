from django.db import models

from mygpo.core.models import UUIDModel
from mygpo.podcasts.models import Podcast


class MergeQueue(UUIDModel):
    """ A Group of podcasts that could be merged """

    @property
    def podcasts(self):
        """ Returns the podcasts of the queue, sorted by subscribers """
        podcasts = [entry.podcast for entry in self.entries.all()]
        podcasts = sorted(podcasts,
                          key=lambda p: p.subscribers, reverse=True)
        return podcasts


class MergeQueueEntry(UUIDModel):
    """ An entry in a MergeQueue """

    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE)

    queue = models.ForeignKey(MergeQueue,
                              on_delete=models.CASCADE,
                              related_name='entries',
                              related_query_name='entry')

    class Meta:
        unique_together = [
            ['podcast', ]  # a podcast can only belong to one queue
        ]
