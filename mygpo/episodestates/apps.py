from django.apps import AppConfig, apps
from django.db.models.signals import post_save


def set_episode_state(sender, **kwargs):
    """Updates the episode state with the saved EpisodeHistoryEntry"""

    from mygpo.episodestates.tasks import update_episode_state

    historyentry = kwargs.get("instance", None)

    if not historyentry:
        return

    update_episode_state.delay(historyentry.pk)


class EpisodeStatesConfig(AppConfig):
    name = "mygpo.episodestates"
    verbose_name = "Episode States"

    def ready(self):
        EpisodeHistoryEntry = apps.get_model("history.EpisodeHistoryEntry")
        post_save.connect(set_episode_state, sender=EpisodeHistoryEntry)
