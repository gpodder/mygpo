from __future__ import unicode_literals

from django.db import models
from django.conf import settings

from mygpo.core.models import UpdateInfoModel
from mygpo.podcasts.models import Episode


class FavoriteEpisode(UpdateInfoModel):

    # the user that has a favorite episode
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    # episode that is the user's favorite
    episode = models.ForeignKey(Episode, db_index=True,
                                on_delete=models.PROTECT)

    class Meta:
        unique_together = [
            ('user', 'episode'),
        ]

    @classmethod
    def episodes_for_user(cls, user):
        """ Favorite episodes of the given user

        Returns the episodes directly, not the FavoriteEpisode objects """
        return Episode.objects.filter(favoriteepisode__user=user)\
                              .select_related('podcast')\
                              .prefetch_related('slugs', 'podcast__slugs')
