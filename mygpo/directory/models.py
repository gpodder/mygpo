from django.db import models

from mygpo.podcasts.models import Podcast
from mygpo.core.models import UpdateInfoModel, OrderedModel


class ExamplePodcastsManager(models.Manager):
    """Manager fo the ExamplePodcast model"""

    def get_podcasts(self):
        """The example podcasts"""
        return Podcast.objects.filter(examplepodcast__isnull=False).order_by(
            "examplepodcast__order"
        )


class ExamplePodcast(UpdateInfoModel, OrderedModel):
    """Example podcasts returned by the API"""

    podcast = models.ForeignKey(Podcast, on_delete=models.CASCADE)

    objects = ExamplePodcastsManager()

    class Meta(OrderedModel.Meta):
        unique_together = [("order",)]
