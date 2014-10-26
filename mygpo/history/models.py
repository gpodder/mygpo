from __future__ import unicode_literals
from collections import Counter

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


class EpisodeHistoryEntry(models.Model):

    DOWNLOAD = 'download'
    PLAY = 'play'
    DELETE = 'delete'
    NEW = 'new'
    FLATTR = 'flattr'
    EPISODE_ACTIONS = (
        (DOWNLOAD, 'downloaded'),
        (PLAY, 'played'),
        (DELETE, 'deleted'),
        (NEW, 'marked as new'),
        (FLATTR, 'flattr\'d'),
    )

    # the timestamp at which the event happened (provided by the client)
    timestamp = models.DateTimeField()

    # the timestamp at which the event was created (provided by the server)
    created = models.DateTimeField(auto_now_add=True)

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
        max_length=max(map(len, [action for action, name in EPISODE_ACTIONS])),
        choices=EPISODE_ACTIONS,
    )

    # the URLs that were used to reference the podcast / episode
    podcast_ref_url = models.URLField(null=True, blank=False, max_length=2048)
    episode_ref_url = models.URLField(null=True, blank=False, max_length=2048)

    # position (in seconds from the beginning) at which playback was started
    started = models.IntegerField(null=True)

    # position (in seconds from the beginning) at which playback was stopped
    stopped = models.IntegerField(null=True)

    # duration (in seconds) of the episode
    total = models.IntegerField(null=True)

    class Meta:
        index_together = [
            ['user', 'client', 'episode', 'action', 'timestamp'],

            # see query in played_episode_counts()
            ['user', 'action', 'episode'],

            ['user', 'episode', 'timestamp'],

            ['episode', 'timestamp'],
        ]

        ordering = ['-timestamp']

        verbose_name_plural = "Episode History Entries"
