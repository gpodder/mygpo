from django.db import models
from django.conf import settings

from mygpo.podcasts.models import Episode
from mygpo.history.models import EpisodeHistoryEntry


class EpisodeState(models.Model):
    """The latest status of an episode for a user"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)

    # the latest action
    action = models.CharField(
        max_length=max(
            map(len, [action for action, name in EpisodeHistoryEntry.EPISODE_ACTIONS])
        ),
        choices=EpisodeHistoryEntry.EPISODE_ACTIONS,
    )

    # the timestamp at which the event happened (provided by the client)
    timestamp = models.DateTimeField()

    class Meta:
        unique_together = [("user", "episode")]

    @classmethod
    def dict_for_user(cls, user, episodes=None):
        """The state of the users episode as a {episode: state} dict"""
        states = cls.objects.filter(user=user)

        if episodes is not None:
            states = states.filter(episode__in=episodes)

        return dict(states.values_list("episode", "action"))
