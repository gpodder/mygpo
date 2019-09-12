from collections import Counter
from datetime import datetime

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from mygpo.podcasts.models import Podcast, Episode
from mygpo.users.models import Client

import logging

logger = logging.getLogger(__name__)


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
    podcast = models.ForeignKey(Podcast, db_index=True, on_delete=models.CASCADE)

    # the user which caused / triggered the event
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, db_index=True, on_delete=models.CASCADE
    )

    # the client on / for which the event happened
    client = models.ForeignKey(Client, null=True, on_delete=models.CASCADE)

    # the action that happened
    action = models.CharField(
        max_length=max(map(len, [action for action, name in PODCAST_ACTIONS])),
        choices=PODCAST_ACTIONS,
    )

    class Meta:
        index_together = [['user', 'client'], ['user', 'podcast']]

        ordering = ['-timestamp']

        verbose_name_plural = "History Entries"


SUBSCRIPTION_ACTIONS = (HistoryEntry.SUBSCRIBE, HistoryEntry.UNSUBSCRIBE)


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
    episode = models.ForeignKey(
        Episode, db_index=True, null=True, on_delete=models.CASCADE
    )

    # the user which caused / triggered the event
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, db_index=True, on_delete=models.CASCADE
    )

    # the client on / for which the event happened
    client = models.ForeignKey(Client, null=True, blank=True, on_delete=models.CASCADE)

    # the action that happened
    action = models.CharField(
        max_length=max(map(len, [action for action, name in EPISODE_ACTIONS])),
        choices=EPISODE_ACTIONS,
    )

    # the URLs that were used to reference the podcast / episode
    podcast_ref_url = models.URLField(null=True, blank=True, max_length=2048)
    episode_ref_url = models.URLField(null=True, blank=True, max_length=2048)

    # position (in seconds from the beginning) at which playback was started
    started = models.IntegerField(null=True, blank=True)

    # position (in seconds from the beginning) at which playback was stopped
    stopped = models.IntegerField(null=True, blank=True)

    # duration (in seconds) of the episode
    total = models.IntegerField(null=True, blank=True)

    class Meta:
        index_together = [
            ['user', 'client', 'episode', 'action', 'timestamp'],
            # see query in played_episode_counts()
            ['user', 'action', 'episode'],
            ['user', 'episode', 'timestamp'],
            ['user', 'timestamp'],
            ['episode', 'timestamp'],
        ]

        ordering = ['-timestamp']

        verbose_name_plural = "Episode History Entries"

    def clean(self):
        """ Validates allowed combinations of time-values """
        PLAY_ACTION_KEYS = ('started', 'stopped', 'total')

        # Key found, but must not be supplied (no play action!)
        if self.action != EpisodeHistoryEntry.PLAY:
            for key in PLAY_ACTION_KEYS:
                if getattr(self, key, None) is not None:
                    raise ValidationError('%s only allowed in "play" entries' % key)

        # Sanity check: If started or total are given, require stopped
        if (
            (self.started is not None) or (self.total is not None)
        ) and self.stopped is None:
            raise ValidationError('started and total require position')

        # Sanity check: total and playmark can only appear together
        if ((self.total is not None) or (self.started is not None)) and (
            (self.total is None) or (self.started is None)
        ):
            raise ValidationError('total and started can only appear together')

    @classmethod
    def create_entry(
        cls,
        user,
        episode,
        action,
        client=None,
        timestamp=None,
        started=None,
        stopped=None,
        total=None,
        podcast_ref_url=None,
        episode_ref_url=None,
    ):

        exists = cls.objects.filter(
            user=user,
            episode=episode,
            client=client,
            action=action,
            started=started,
            stopped=stopped,
        ).exists()
        if exists:
            logger.warning(
                'Trying to save duplicate {cls} for {user} '
                '/ {episode}'.format(cls=cls, user=user, episode=episode)
            )
            # if such an entry already exists, do nothing
            return

        entry = cls(user=user, episode=episode, action=action)

        if client:
            entry.client = client

        if started is not None:
            entry.started = started

        if stopped is not None:
            entry.stopped = stopped

        if total is not None:
            entry.total = total

        if timestamp is None:
            entry.timestamp = datetime.utcnow()
        else:
            entry.timestamp = timestamp

        if podcast_ref_url:
            entry.podcast_ref_url = podcast_ref_url

        if episode_ref_url:
            entry.episode_ref_url = episode_ref_url

        try:
            entry.full_clean()
            entry.save()
            return entry

        except ValidationError as e:
            logger.warning(
                'Validation of {cls} failed for {user}: {err}'.format(
                    cls=cls, user=user, err=e
                )
            )
            return None
