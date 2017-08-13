from django.db import models

from mygpo.core.models import UUIDModel
from mygpo.podcasts.models import Podcast


class MergeTask(UUIDModel):
    """ A Group of podcasts that could be merged """

    @property
    def podcasts(self):
        """ Returns the podcasts of the task, sorted by subscribers """
        podcasts = [entry.podcast for entry in self.entries.all()]
        podcasts = sorted(podcasts,
                          key=lambda p: p.subscribers, reverse=True)
        return podcasts


class MergeTaskEntry(UUIDModel):
    """ An entry in a MergeTask """

    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE)

    task = models.ForeignKey(MergeTask,
                              on_delete=models.CASCADE,
                              related_name='entries',
                              related_query_name='entry')

    class Meta:
        unique_together = [
            ['podcast', ]  # a podcast can only belong to one task
        ]
