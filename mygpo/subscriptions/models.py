from django.db import models
from django.conf import settings

from mygpo.core.models import UpdateInfoModel, DeleteableModel, SettingsModel
from mygpo.users.models import Client
from mygpo.podcasts.models import Podcast


class SubscriptionManager(models.Manager):
    """ Manages subscriptions """

    def subscribe(self, device, podcast):
        # create subscription, add history
        pass

    def unsubscribe(self, device, podcast):
        # delete subscription, add history
        pass


class Subscription(DeleteableModel):
    """ A subscription to a podcast on a specific client """

    # the user that subscribed to a podcast
    user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True,
                             on_delete=models.CASCADE)

    # the client on which the user subscribed to the podcast
    client = models.ForeignKey(Client, db_index=True,
                               on_delete=models.CASCADE)

    # the podcast to which the user subscribed to
    podcast = models.ForeignKey(Podcast, db_index=True,
                                on_delete=models.PROTECT)

    # the URL that the user subscribed to; a podcast might have multiple URLs,
    # the we want to return the users the ones they know
    ref_url = models.URLField(max_length=2048)

    # the following fields do not use auto_now[_add] for the time of the
    # migration, in order to store historically accurate data; once the
    # migration is complete, this model should inherit from UpdateInfoModel
    created = models.DateTimeField()
    modified = models.DateTimeField()

    objects = SubscriptionManager()

    class Meta:
        unique_together = [
            ['user', 'client', 'podcast'],
        ]

        index_together = [
            ['user', 'client']
        ]


class PodcastConfig(SettingsModel, UpdateInfoModel):
    """ Settings for a podcast, independant of a device / subscription """

    # the user for which the config is stored
    user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True,
                             on_delete=models.CASCADE)

    # the podcast for which the config is stored
    podcast = models.ForeignKey(Podcast, db_index=True,
                                on_delete=models.PROTECT)
