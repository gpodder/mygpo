from mygpo.episodestates.tasks import update_episode_state

default_app_config = 'mygpo.episodestates.apps.EpisodeStatesConfig'

def set_episode_state(sender, **kwargs):
    """ Updates the episode state with the saved EpisodeHistoryEntry """

    historyentry = kwargs.get('instance', None)

    if not historyentry:
        return

    update_episode_state.delay(historyentry.pk)
