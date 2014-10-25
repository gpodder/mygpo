from django.apps import AppConfig
from django.db.models.signals import post_save

from mygpo.history.models import EpisodeHistoryEntry
from mygpo.episodestates import set_episode_state


class EpisodeStatesConfig(AppConfig):
    name = 'mygpo.episodestates'
    verbose_name = 'Episode States'

    def ready(self):
        post_save.connect(set_episode_state, sender=EpisodeHistoryEntry)
