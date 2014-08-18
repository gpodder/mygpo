from __future__ import unicode_literals

from django.db import models
from django.conf import settings

from mygpo.podcasts.models import Podcast, Episode
from mygpo.users.models import Client


class HistoryEntry(models.Model):
    """ A entry in the history """

    SUBSCRIBE = 'subscribe'
    UNSUBSCRIBE = 'unsubscribe'
    FLATTR = 'flattr'
    PODCAST_ACTIONS = (
        (SUBSCRIBE, 'subscribed'),
        (UNSUBSCRIBE, 'unsubscribed'),
        (FLATTR, 'flattr\'d'),
    )

    # the timestamp at which the event happened
    timestamp = models.DateTimeField()


    # the podcast which was involved in the event
    podcast = models.ForeignKey(Podcast, db_index=True,
                                on_delete=models.CASCADE)

    # the episode which was involved in the event
    episode = models.ForeignKey(Episode, db_index=True, null=True,
                                on_delete=models.CASCADE)

    # the user which caused / triggered the event
    user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True,
                             on_delete=models.CASCADE)

    # the client on / for which the event happened
    client = models.ForeignKey(Client, null=True, on_delete=models.CASCADE)

    # the action that happened
    action = models.CharField(
        max_length=max(map(len, [action for action, name in PODCAST_ACTIONS])),
        choices=PODCAST_ACTIONS,
    )

    class Meta:
        index_together = [
            ['user', 'client'],
            ['user', 'podcast'],
        ]

        ordering = ['-timestamp']

        verbose_name_plural = "History Entries"
