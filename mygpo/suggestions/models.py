from django.db import models
from django.conf import settings

from mygpo.core.models import UpdateInfoModel, DeleteableModel
from mygpo.podcasts.models import Podcast


class PodcastSuggestion(UpdateInfoModel, DeleteableModel):
    """ A podcast which is suggested to a user

    A suggestion can be marked as "unwanted" by a user by deleting it. """

    # the user to which the podcast has been suggested
    suggested_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # the podcast which has been suggested to the above user
    podcast = models.ForeignKey(Podcast, on_delete=models.PROTECT)

    class Meta:
        unique_together = [('suggested_to', 'podcast')]
